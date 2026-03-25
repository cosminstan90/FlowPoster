"""
Webhook endpoints for n8n / external integrations.

Authentication: X-API-Key header with a valid, active API key.
Each endpoint checks the required scope.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.api_key import APIKey
from backend.models import Campaign, GeneratedPage, Keyword
from backend.schemas.common import APIResponse
from backend.services.duplicate_guard import DuplicateGuard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# ---------------------------------------------------------------------------
# API Key auth dependency
# ---------------------------------------------------------------------------

import bcrypt


async def _resolve_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    # Find candidates by prefix (first 10 chars)
    prefix = x_api_key[:10]
    rows = await db.execute(
        select(APIKey).where(APIKey.key_prefix == prefix, APIKey.is_active == True)
    )
    candidates = rows.scalars().all()

    for row in candidates:
        if bcrypt.checkpw(x_api_key.encode(), row.key_hash.encode()):
            # Update last_used_at
            row.last_used_at = datetime.now(timezone.utc)
            await db.flush()
            return row

    raise HTTPException(status_code=401, detail="Invalid or revoked API key")


def require_scope(scope: str):
    async def _dep(api_key: APIKey = Depends(_resolve_api_key)) -> APIKey:
        scopes = json.loads(api_key.scopes)
        if scope not in scopes:
            raise HTTPException(
                status_code=403,
                detail=f"API key missing required scope: '{scope}'"
            )
        return api_key
    return _dep


# ---------------------------------------------------------------------------
# Helper: import rows into a campaign (shared logic)
# ---------------------------------------------------------------------------

async def _import_keyword_rows(
    campaign_id: uuid.UUID,
    rows: list[dict],
    db: AsyncSession,
) -> dict[str, int]:
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    guard = await DuplicateGuard.build(campaign_id, db)
    now = datetime.now(timezone.utc)
    to_insert: list[Keyword] = []
    imported = skipped = duplicates = 0

    for row in rows:
        raw = str(row.get("keyword", "")).strip()
        if not raw:
            skipped += 1
            continue
        result = guard.check(raw)
        if result.is_duplicate:
            duplicates += 1
            continue
        to_insert.append(
            Keyword(
                campaign_id=campaign_id,
                keyword=raw[:500],
                search_intent=row.get("search_intent") or None,
                page_type=row.get("page_type") or None,
                search_volume=_safe_int(row.get("search_volume")),
                keyword_difficulty=_safe_int(row.get("keyword_difficulty")),
                source="webhook",
                updated_at=now,
            )
        )
        guard.accept(raw)
        imported += 1

    if to_insert:
        db.add_all(to_insert)
        await db.flush()

    return {"imported": imported, "skipped": skipped, "duplicates": duplicates}


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(str(val).replace(",", "").split(".")[0])
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class ImportBody(APIResponse):
    pass


from pydantic import BaseModel


class WebhookImportRequest(BaseModel):
    campaign_id: uuid.UUID
    keywords: list[dict]  # [{keyword, search_intent?, search_volume?, ...}]


class SheetsImportRequest(BaseModel):
    campaign_id: uuid.UUID
    spreadsheet_id: str
    sheet_name: str = "Sheet1"
    keyword_column: str = "A"
    start_row: int = 2


class ApproveAllRequest(BaseModel):
    campaign_id: uuid.UUID


@router.post("/import", response_model=APIResponse[dict])
async def webhook_import(
    body: WebhookImportRequest,
    db: AsyncSession = Depends(get_db),
    _key: APIKey = Depends(require_scope("import_keywords")),
):
    """Import a list of keywords into a campaign via webhook."""
    stats = await _import_keyword_rows(body.campaign_id, body.keywords, db)

    from backend.services.telegram_service import send_telegram
    await send_telegram(
        f"📥 <b>Import webhook</b>\n"
        f"Campaign: <code>{body.campaign_id}</code>\n"
        f"Importate: {stats['imported']} · Duplicate: {stats['duplicates']}"
    )

    return APIResponse.ok(data=stats, message=f"Imported {stats['imported']} keywords")


@router.post("/import/sheets", response_model=APIResponse[dict])
async def webhook_import_sheets(
    body: SheetsImportRequest,
    db: AsyncSession = Depends(get_db),
    _key: APIKey = Depends(require_scope("import_keywords")),
):
    """Import keywords from a public Google Sheet (read via Sheets API or CSV export)."""
    from backend.config import settings

    sheets_key = getattr(settings, "GOOGLE_SHEETS_API_KEY", "")
    if not sheets_key:
        # Fallback: use CSV export (works for public sheets)
        csv_url = (
            f"https://docs.google.com/spreadsheets/d/{body.spreadsheet_id}"
            f"/gviz/tq?tqx=out:csv&sheet={body.sheet_name}"
        )
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(csv_url)
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to fetch Google Sheet: {exc}")

        import csv, io
        text = resp.text
        reader = csv.DictReader(io.StringIO(text))
        fieldnames = reader.fieldnames or []

        # Map column letter to actual header
        col_idx = ord(body.keyword_column.upper()) - ord("A")
        if col_idx < 0 or col_idx >= len(fieldnames):
            raise HTTPException(status_code=422, detail=f"Column '{body.keyword_column}' out of range. Found columns: {fieldnames}")

        kw_col = fieldnames[col_idx]
        rows = []
        for i, row in enumerate(reader, start=2):
            if i < body.start_row:
                continue
            kw = row.get(kw_col, "").strip()
            if kw:
                rows.append({"keyword": kw})
    else:
        # Use Sheets API v4
        range_notation = f"{body.sheet_name}!{body.keyword_column}{body.start_row}:{body.keyword_column}10000"
        url = (
            f"https://sheets.googleapis.com/v4/spreadsheets/{body.spreadsheet_id}"
            f"/values/{range_notation}?key={sheets_key}"
        )
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Failed to fetch Google Sheet: {exc}")

        values = data.get("values", [])
        rows = [{"keyword": row[0].strip()} for row in values if row and row[0].strip()]

    stats = await _import_keyword_rows(body.campaign_id, rows, db)

    from backend.services.telegram_service import send_telegram
    await send_telegram(
        f"📊 <b>Import Google Sheets</b>\n"
        f"Sheet: <code>{body.spreadsheet_id}</code>\n"
        f"Importate: {stats['imported']} · Duplicate: {stats['duplicates']}"
    )

    return APIResponse.ok(data=stats, message=f"Imported {stats['imported']} keywords from Google Sheets")


@router.get("/campaign/{campaign_id}/status", response_model=APIResponse[dict])
async def webhook_campaign_status(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _key: APIKey = Depends(require_scope("read_campaigns")),
):
    """Return keyword status counts for a campaign."""
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    rows = await db.execute(
        select(Keyword.status, Campaign.id)
        .join(Campaign, Campaign.id == Keyword.campaign_id)
        .where(Keyword.campaign_id == campaign_id)
    )
    # Count per status
    from sqlalchemy import func
    count_rows = await db.execute(
        select(Keyword.status, func.count(Keyword.id).label("cnt"))
        .where(Keyword.campaign_id == campaign_id)
        .group_by(Keyword.status)
    )
    counts = {row.status: row.cnt for row in count_rows}

    return APIResponse.ok(
        data={
            "campaign_id": str(campaign_id),
            "campaign_name": campaign.name,
            "status_counts": counts,
        },
        message="Campaign status"
    )


@router.post("/approve-all/{campaign_id}", response_model=APIResponse[dict])
async def webhook_approve_all(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _key: APIKey = Depends(require_scope("publish_pages")),
):
    """Approve all draft pages in a campaign (set status → approved)."""
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    draft_pages = (
        await db.execute(
            select(GeneratedPage)
            .join(Keyword, Keyword.id == GeneratedPage.keyword_id)
            .where(
                Keyword.campaign_id == campaign_id,
                GeneratedPage.status == "draft",
            )
        )
    ).scalars().all()

    now = datetime.now(timezone.utc)
    approved_count = 0
    for page in draft_pages:
        page.status = "approved"
        page.updated_at = now
        approved_count += 1

    await db.flush()

    from backend.services.telegram_service import send_telegram
    await send_telegram(
        f"✅ <b>Aprobare bulk</b>\n"
        f"Campaign: <code>{campaign.name}</code>\n"
        f"{approved_count} pagini aprobate prin webhook"
    )

    return APIResponse.ok(
        data={"approved": approved_count},
        message=f"Approved {approved_count} pages"
    )
