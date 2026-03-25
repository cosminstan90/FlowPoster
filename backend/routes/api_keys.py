from __future__ import annotations

import json
import os
import secrets
import uuid
from datetime import datetime, timezone

import bcrypt
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from backend.deps import CurrentUser, DB
from backend.models.api_key import APIKey
from backend.schemas.api_key import APIKeyCreate, APIKeyCreated, APIKeyOut
from backend.schemas.common import APIResponse

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def _hash_key(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()


def _verify_key(raw: str, hashed: str) -> bool:
    return bcrypt.checkpw(raw.encode(), hashed.encode())


def _mask(key: str) -> str:
    """Return 'sk-XXXXXXXX...last4' style masked key."""
    return f"{key[:10]}...{key[-4:]}"


def _row_to_out(row: APIKey) -> APIKeyOut:
    return APIKeyOut(
        id=row.id,
        name=row.name,
        key_masked=f"{row.key_prefix}...{row.key_prefix[-4:]}",
        scopes=json.loads(row.scopes),
        project_id=row.project_id,
        is_active=row.is_active,
        last_used_at=row.last_used_at,
        created_at=row.created_at,
    )


@router.get("", response_model=APIResponse[list[APIKeyOut]])
async def list_api_keys(_: CurrentUser, db: DB):
    rows = await db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
    items = [_row_to_out(r) for r in rows.scalars().all()]
    return APIResponse.ok(data=items, message=f"{len(items)} API keys")


@router.post("", response_model=APIResponse[APIKeyCreated], status_code=status.HTTP_201_CREATED)
async def create_api_key(body: APIKeyCreate, _: CurrentUser, db: DB):
    try:
        scopes = body.validated_scopes()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    raw_key = "sk-" + secrets.token_urlsafe(32)
    key_hash = _hash_key(raw_key)
    prefix = raw_key[:10]  # "sk-XXXXXXX" (10 chars)

    row = APIKey(
        id=uuid.uuid4(),
        name=body.name,
        key_hash=key_hash,
        key_prefix=prefix,
        scopes=json.dumps(scopes),
        project_id=body.project_id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)

    result = APIKeyCreated(
        id=row.id,
        name=row.name,
        key_masked=_mask(raw_key),
        scopes=scopes,
        project_id=row.project_id,
        is_active=row.is_active,
        last_used_at=row.last_used_at,
        created_at=row.created_at,
        full_key=raw_key,
    )
    return APIResponse.ok(data=result, message="API key created. Copy the full key — it won't be shown again.")


@router.delete("/{key_id}", response_model=APIResponse[None])
async def revoke_api_key(key_id: uuid.UUID, _: CurrentUser, db: DB):
    row = await db.scalar(select(APIKey).where(APIKey.id == key_id))
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    row.is_active = False
    await db.flush()
    return APIResponse.ok(data=None, message="API key revoked")
