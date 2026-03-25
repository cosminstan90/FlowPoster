from __future__ import annotations

import csv
import io
import json
import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import CurrentUser, DB
from backend.models import Campaign, Keyword
from backend.schemas.common import APIResponse
from backend.schemas.keyword import (
    ImportPasteRequest,
    ImportResult,
    KeywordCreate,
    KeywordOut,
    KeywordStatusUpdate,
    PaginatedKeywords,
)
from backend.services.duplicate_guard import DuplicateGuard

router = APIRouter(prefix="/keywords", tags=["keywords"])

_DELETABLE_STATUSES = {"pending", "error"}

# ---------------------------------------------------------------------------
# Source presets — maps internal field names → CSV column header names
# ---------------------------------------------------------------------------
_SOURCE_PRESETS: dict[str, dict[str, str]] = {
    "ahrefs": {
        "keyword": "Keyword",
        "search_volume": "Volume",
        "keyword_difficulty": "KD",
        "cpc_usd": "CPC",
    },
    "semrush": {
        "keyword": "Keyword",
        "search_volume": "Search Volume",
        "keyword_difficulty": "Keyword Difficulty",
        "cpc_usd": "CPC",
    },
    "gsc": {
        "keyword": "query",
        "search_volume": "impressions",
    },
}


def _apply_mapping(row: dict, col_map: dict[str, str]) -> dict:
    """
    Given a raw CSV row and a {field: csv_column} mapping, return a normalised
    dict with internal field names as keys.
    """
    out: dict = {}
    for field, col in col_map.items():
        if col and col in row:
            out[field] = row[col]
    # Pass through any column already named after an internal field
    for field in ("keyword", "search_intent", "page_type", "search_volume",
                  "keyword_difficulty", "cpc_usd"):
        if field not in out and field in row:
            out[field] = row[field]
    return out


def _to_int(val: str | None) -> int | None:
    if not val:
        return None
    try:
        # Strip commas (e.g. "1,234"), dots used as thousands sep
        clean = val.replace(",", "").replace(" ", "").split(".")[0]
        return int(clean)
    except (ValueError, AttributeError):
        return None


def _to_decimal(val: str | None) -> Decimal | None:
    if not val:
        return None
    try:
        clean = val.replace(",", "").replace(" ", "").replace("$", "")
        return Decimal(clean)
    except (InvalidOperation, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Shared import logic
# ---------------------------------------------------------------------------

async def _run_import(
    campaign_id: uuid.UUID,
    rows: list[dict],
    db: AsyncSession,
    source: str = "manual",
) -> ImportResult:
    """Validate campaign, run duplicate checks, bulk insert, return stats."""
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    guard = await DuplicateGuard.build(campaign_id, db)

    now = datetime.now(timezone.utc)
    to_insert: list[Keyword] = []
    imported = skipped = duplicates = 0
    warnings: list[str] = []

    for row in rows:
        raw = row.get("keyword", "").strip()
        if not raw:
            skipped += 1
            continue

        result = guard.check(raw)

        if result.is_duplicate:
            duplicates += 1
            continue

        if result.cross_campaign_warning:
            warnings.append(result.cross_campaign_warning)

        to_insert.append(
            Keyword(
                campaign_id=campaign_id,
                keyword=raw[:500],
                search_intent=row.get("search_intent") or None,
                page_type=row.get("page_type") or None,
                search_volume=_to_int(str(row["search_volume"])) if row.get("search_volume") is not None else None,
                keyword_difficulty=_to_int(str(row["keyword_difficulty"])) if row.get("keyword_difficulty") is not None else None,
                cpc_usd=_to_decimal(str(row["cpc_usd"])) if row.get("cpc_usd") is not None else None,
                source=source,
                updated_at=now,
            )
        )
        guard.accept(raw)
        imported += 1

    if to_insert:
        db.add_all(to_insert)
        await db.flush()

    return ImportResult(
        imported=imported,
        skipped=skipped,
        duplicates=duplicates,
        cross_campaign_warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/import/csv",
    response_model=APIResponse[ImportResult],
    status_code=status.HTTP_200_OK,
)
async def import_csv(
    campaign_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    column_mapping: str | None = Form(None),
    source: str = Form("manual"),
    _: CurrentUser,
    db: DB,
):
    """
    Import keywords from a CSV file.

    ``column_mapping`` is an optional JSON string mapping internal field names to
    CSV column headers, e.g.::

        {"keyword": "Keyword", "search_volume": "Volume", "keyword_difficulty": "KD", "cpc_usd": "CPC"}

    ``source`` is a free-form tag (e.g. "ahrefs", "semrush", "gsc", "manual").
    If ``source`` matches a known preset and no ``column_mapping`` is supplied,
    the preset mapping is used automatically.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    # Resolve column mapping: explicit > preset > identity
    col_map: dict[str, str] = {}
    if column_mapping:
        try:
            col_map = json.loads(column_mapping)
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="column_mapping must be valid JSON")
    elif source in _SOURCE_PRESETS:
        col_map = _SOURCE_PRESETS[source]

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []

    # Determine actual keyword column
    kw_col = col_map.get("keyword", "keyword")
    if kw_col not in fieldnames:
        raise HTTPException(
            status_code=422,
            detail=f"CSV column '{kw_col}' not found. Available columns: {fieldnames}",
        )

    rows = [_apply_mapping(dict(r), col_map) for r in reader]

    result = await _run_import(campaign_id, rows, db, source=source)
    return APIResponse.ok(
        data=result,
        message=f"Imported {result.imported}, skipped {result.skipped}, duplicates {result.duplicates}",
    )


@router.post(
    "/import/paste",
    response_model=APIResponse[ImportResult],
    status_code=status.HTTP_200_OK,
)
async def import_paste(
    body: ImportPasteRequest,
    _: CurrentUser,
    db: DB,
):
    rows = [{"keyword": line.strip()} for line in body.text.splitlines() if line.strip()]
    result = await _run_import(body.campaign_id, rows, db)
    return APIResponse.ok(
        data=result,
        message=f"Imported {result.imported}, skipped {result.skipped}, duplicates {result.duplicates}",
    )


@router.post(
    "/manual",
    response_model=APIResponse[KeywordOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_keyword(
    body: KeywordCreate,
    _: CurrentUser,
    db: DB,
):
    campaign = await db.scalar(select(Campaign).where(Campaign.id == body.campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    guard = await DuplicateGuard.build(body.campaign_id, db)
    result = guard.check(body.keyword)

    if result.is_duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A similar keyword already exists in this campaign (similarity > 85%)",
        )

    now = datetime.now(timezone.utc)
    kw = Keyword(
        campaign_id=body.campaign_id,
        keyword=body.keyword,
        search_intent=body.search_intent,
        page_type=body.page_type,
        search_volume=body.search_volume,
        keyword_difficulty=body.keyword_difficulty,
        cpc_usd=body.cpc_usd,
        source=body.source,
        updated_at=now,
    )
    db.add(kw)
    await db.flush()
    await db.refresh(kw)

    msg = "Keyword created"
    if result.cross_campaign_warning:
        msg = f"{msg}. Warning: {result.cross_campaign_warning}"

    return APIResponse.ok(data=KeywordOut.model_validate(kw), message=msg)


@router.get("", response_model=APIResponse[PaginatedKeywords])
async def list_keywords(
    campaign_id: uuid.UUID = Query(...),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    sort: str = Query("volume", description="volume | created"),
    _: CurrentUser,
    db: DB,
):
    base = select(Keyword).where(Keyword.campaign_id == campaign_id)
    if status_filter:
        base = base.where(Keyword.status == status_filter)

    total: int = await db.scalar(
        select(func.count()).select_from(base.subquery())
    ) or 0

    # Sort order: volume desc (nulls last) or created desc
    if sort == "volume":
        order = Keyword.search_volume.desc().nulls_last()
    else:
        order = Keyword.created_at.desc()

    offset = (page - 1) * limit
    rows = await db.execute(base.order_by(order).offset(offset).limit(limit))
    items = [KeywordOut.model_validate(k) for k in rows.scalars().all()]

    return APIResponse.ok(
        data=PaginatedKeywords(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=max(1, math.ceil(total / limit)),
        ),
        message=f"{total} keywords",
    )


@router.delete("/{keyword_id}", response_model=APIResponse[None])
async def delete_keyword(
    keyword_id: uuid.UUID,
    _: CurrentUser,
    db: DB,
):
    kw = await db.scalar(select(Keyword).where(Keyword.id == keyword_id))
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")

    if kw.status not in _DELETABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete keyword with status '{kw.status}'. Only pending/error keywords may be deleted.",
        )

    await db.delete(kw)
    return APIResponse.ok(data=None, message="Keyword deleted")


@router.put("/{keyword_id}/status", response_model=APIResponse[KeywordOut])
async def update_keyword_status(
    keyword_id: uuid.UUID,
    body: KeywordStatusUpdate,
    _: CurrentUser,
    db: DB,
):
    kw = await db.scalar(select(Keyword).where(Keyword.id == keyword_id))
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")

    kw.status = body.status
    kw.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(kw)
    return APIResponse.ok(
        data=KeywordOut.model_validate(kw),
        message=f"Status updated to '{body.status}'",
    )
