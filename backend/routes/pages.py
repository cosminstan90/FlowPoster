"""
Routes for GeneratedPage: view, edit, status, image search, section regeneration.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.deps import CurrentUser, DB
from backend.models.campaign import Campaign
from backend.models.generated_page import GeneratedPage
from backend.models.keyword import Keyword
from backend.models.project import Project
from backend.schemas.common import APIResponse
from backend.schemas.page import (
    BreadcrumbContext,
    FindImageResult,
    PageDetailOut,
    PageStatusUpdate,
    PageUpdateRequest,
    RegenerateRequest,
)
from backend.services.image_finder import find_image

router = APIRouter(prefix="/pages", tags=["pages"])

ALLOWED_STATUSES = {"draft", "approved", "published", "rejected"}


# ------------------------------------------------------------------ helpers --

async def _get_page_with_breadcrumb(page_id: uuid.UUID, db) -> tuple[GeneratedPage, BreadcrumbContext]:
    stmt = (
        select(GeneratedPage)
        .where(GeneratedPage.id == page_id)
        .options(
            selectinload(GeneratedPage.keyword).selectinload(Keyword.campaign)
        )
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    keyword = page.keyword
    campaign = keyword.campaign

    # Fetch project
    proj_result = await db.execute(select(Project).where(Project.id == campaign.project_id))
    project = proj_result.scalar_one_or_none()

    breadcrumb = BreadcrumbContext(
        project_id=project.id if project else campaign.project_id,
        project_name=project.name if project else "—",
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        keyword_text=keyword.keyword,
    )
    return page, breadcrumb


# ------------------------------------------------------------------ routes ---

@router.get("/by-keyword/{keyword_id}", response_model=APIResponse[PageDetailOut])
async def get_page_by_keyword(keyword_id: uuid.UUID, _: CurrentUser, db: DB):
    stmt = (
        select(GeneratedPage)
        .where(GeneratedPage.keyword_id == keyword_id)
        .order_by(GeneratedPage.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="No page for this keyword")

    _, breadcrumb = await _get_page_with_breadcrumb(page.id, db)
    out = PageDetailOut.model_validate(page)
    out.breadcrumb = breadcrumb
    return APIResponse.ok(out)


@router.get("/{page_id}", response_model=APIResponse[PageDetailOut])
async def get_page(page_id: uuid.UUID, _: CurrentUser, db: DB):
    page, breadcrumb = await _get_page_with_breadcrumb(page_id, db)
    out = PageDetailOut.model_validate(page)
    out.breadcrumb = breadcrumb
    return APIResponse.ok(out)


@router.put("/{page_id}", response_model=APIResponse[PageDetailOut])
async def update_page(page_id: uuid.UUID, body: PageUpdateRequest, _: CurrentUser, db: DB):
    page, breadcrumb = await _get_page_with_breadcrumb(page_id, db)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(page, field, value)

    await db.commit()
    await db.refresh(page)
    out = PageDetailOut.model_validate(page)
    out.breadcrumb = breadcrumb
    return APIResponse.ok(out, "Page updated")


@router.put("/{page_id}/status", response_model=APIResponse[PageDetailOut])
async def update_page_status(page_id: uuid.UUID, body: PageStatusUpdate, _: CurrentUser, db: DB):
    if body.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status '{body.status}'")

    page, breadcrumb = await _get_page_with_breadcrumb(page_id, db)
    page.status = body.status
    now = datetime.now(timezone.utc)
    if body.status == "approved":
        page.approved_at = now
    elif body.status == "published":
        page.published_at = now

    # Sync keyword status
    keyword = page.keyword
    if body.status in ("approved", "published"):
        keyword.status = body.status

    await db.commit()
    await db.refresh(page)
    out = PageDetailOut.model_validate(page)
    out.breadcrumb = breadcrumb
    return APIResponse.ok(out, f"Status updated to {body.status}")


@router.post("/{page_id}/find-image", response_model=APIResponse[FindImageResult])
async def find_page_image(page_id: uuid.UUID, _: CurrentUser, db: DB):
    page, breadcrumb = await _get_page_with_breadcrumb(page_id, db)
    query = f"{breadcrumb.keyword_text} {breadcrumb.project_name}"
    result = await find_image(query)

    if result:
        page.featured_image_url = result["url"]
        page.featured_image_credit = result["credit"]
        await db.commit()

    return APIResponse.ok(FindImageResult(
        url=result["url"] if result else None,
        credit=result["credit"] if result else None,
    ))


@router.post("/{page_id}/regenerate", response_model=APIResponse[dict])
async def regenerate_section(page_id: uuid.UUID, body: RegenerateRequest, _: CurrentUser, db: DB):
    page, breadcrumb = await _get_page_with_breadcrumb(page_id, db)

    keyword = page.keyword
    campaign = keyword.campaign

    # Gather campaign/project context for prompts
    from sqlalchemy.orm import selectinload as sli
    from backend.models.site_context import SiteContext

    sc_result = await db.execute(
        select(SiteContext).where(SiteContext.project_id == campaign.project_id)
    )
    site_ctx = sc_result.scalar_one_or_none()

    niche = site_ctx.niche if site_ctx else "general"
    tone = site_ctx.tone if site_ctx else "professional"
    language = campaign.language or "English"
    keyword_text = keyword.keyword

    from backend.services.ai.regenerate import regenerate_section as _regen
    updated_fields = await _regen(
        page=page,
        section=body.section,
        language=language,
        niche=niche,
        tone=tone,
        keyword_text=keyword_text,
        db=db,
    )

    await db.commit()
    return APIResponse.ok(updated_fields, f"Section '{body.section}' regenerated")
