"""
Publish routes: single page, unpublish, bulk, and CMS connection test.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.deps import CurrentUser, DB
from backend.models.campaign import Campaign
from backend.models.generated_page import GeneratedPage
from backend.models.keyword import Keyword
from backend.models.project import Project
from backend.schemas.common import APIResponse
from backend.services.cms import get_adapter
from backend.worker.queue import get_arq_pool

router = APIRouter(prefix="/publish", tags=["publish"])


# ------------------------------------------------------------------ helpers --

async def _load_page_and_project(page_id: uuid.UUID, db) -> tuple[GeneratedPage, Project]:
    page = await db.scalar(
        select(GeneratedPage)
        .where(GeneratedPage.id == page_id)
        .options(selectinload(GeneratedPage.keyword).selectinload(Keyword.campaign))
    )
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    campaign = page.keyword.campaign
    project = await db.scalar(select(Project).where(Project.id == campaign.project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return page, project


# ------------------------------------------------------------------ schemas --

class BulkPublishRequest(BaseModel):
    page_ids: list[uuid.UUID]


# ------------------------------------------------------------------ routes ---

@router.post("/page/{page_id}", response_model=APIResponse[dict])
async def publish_page(page_id: uuid.UUID, _: CurrentUser, db: DB):
    page, project = await _load_page_and_project(page_id, db)

    if page.status not in ("draft", "approved"):
        raise HTTPException(
            status_code=409,
            detail=f"Page status is '{page.status}' — only draft/approved pages can be published",
        )

    adapter = get_adapter(project)
    result = await adapter.publish(page)

    if not result["success"]:
        raise HTTPException(status_code=502, detail="CMS publish call returned failure")

    page.status = "published"
    page.published_url = result["published_url"]
    page.published_at = datetime.now(timezone.utc)
    page.keyword.status = "published"
    page.keyword.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return APIResponse.ok(
        {"published_url": result["published_url"], "remote_id": result["remote_id"]},
        "Page published",
    )


@router.post("/unpublish/{page_id}", response_model=APIResponse[dict])
async def unpublish_page(page_id: uuid.UUID, _: CurrentUser, db: DB):
    page, project = await _load_page_and_project(page_id, db)

    if page.status != "published":
        raise HTTPException(
            status_code=409,
            detail=f"Page status is '{page.status}' — only published pages can be unpublished",
        )

    adapter = get_adapter(project)
    result = await adapter.unpublish(page)

    if not result["success"]:
        raise HTTPException(status_code=502, detail="CMS unpublish call returned failure")

    page.status = "approved"
    page.keyword.status = "approved"
    page.keyword.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return APIResponse.ok({}, "Page unpublished (reverted to approved)")


@router.post("/test/{project_id}", response_model=APIResponse[dict])
async def test_connection(project_id: uuid.UUID, _: CurrentUser, db: DB):
    project = await db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    adapter = get_adapter(project)
    result = await adapter.test_connection()
    return APIResponse.ok(
        {"success": result["success"], "message": result["message"]},
        result["message"],
    )


@router.post("/bulk", response_model=APIResponse[dict])
async def bulk_publish(body: BulkPublishRequest, _: CurrentUser, db: DB):
    if not body.page_ids:
        raise HTTPException(status_code=400, detail="page_ids must not be empty")

    # Validate all pages exist and are in a publishable state
    pages = (
        await db.execute(
            select(GeneratedPage).where(GeneratedPage.id.in_(body.page_ids))
        )
    ).scalars().all()

    found_ids = {p.id for p in pages}
    missing = [str(pid) for pid in body.page_ids if pid not in found_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"Pages not found: {missing}")

    not_ready = [str(p.id) for p in pages if p.status not in ("draft", "approved")]
    if not_ready:
        raise HTTPException(
            status_code=409,
            detail=f"These pages are not in draft/approved state: {not_ready}",
        )

    pool = await get_arq_pool()
    enqueued = []
    for page in pages:
        await pool.enqueue_job("publish_page", str(page.id))
        enqueued.append(str(page.id))

    return APIResponse.ok(
        {"enqueued": len(enqueued), "page_ids": enqueued},
        f"Enqueued {len(enqueued)} publish jobs",
    )
