import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import CurrentUser, DB
from backend.models import Project, SiteContext
from backend.schemas.common import APIResponse
from backend.schemas.site_context import SiteContextOut, SiteContextUpsert

router = APIRouter(prefix="/projects/{project_id}/context", tags=["site-context"])


async def _require_project(project_id: uuid.UUID, db: AsyncSession) -> None:
    exists = await db.scalar(select(Project.id).where(Project.id == project_id))
    if not exists:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("", response_model=APIResponse[SiteContextOut])
async def get_context(
    project_id: uuid.UUID,
    _: str = CurrentUser,
    db: AsyncSession = DB,
):
    await _require_project(project_id, db)
    result = await db.execute(
        select(SiteContext).where(SiteContext.project_id == project_id)
    )
    sc = result.scalar_one_or_none()
    if not sc:
        raise HTTPException(status_code=404, detail="Site context not found")
    return APIResponse.ok(data=SiteContextOut.model_validate(sc), message="OK")


@router.put("", response_model=APIResponse[SiteContextOut])
async def upsert_context(
    project_id: uuid.UUID,
    body: SiteContextUpsert,
    _: str = CurrentUser,
    db: AsyncSession = DB,
):
    await _require_project(project_id, db)

    result = await db.execute(
        select(SiteContext).where(SiteContext.project_id == project_id)
    )
    sc = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if sc is None:
        sc = SiteContext(project_id=project_id, updated_at=now, **body.model_dump())
        db.add(sc)
        created = True
    else:
        for field, value in body.model_dump().items():
            setattr(sc, field, value)
        sc.updated_at = now
        created = False

    await db.flush()
    await db.refresh(sc)
    msg = "Site context created" if created else "Site context updated"
    return APIResponse.ok(data=SiteContextOut.model_validate(sc), message=msg)
