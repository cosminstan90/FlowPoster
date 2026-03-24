"""
CRUD routes for PromptTemplate + test endpoint.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from backend.deps import CurrentUser, DB
from backend.models import Campaign
from backend.models.prompt_template import PromptTemplate
from backend.schemas.common import APIResponse
from backend.schemas.template import (
    TemplateCreate,
    TemplateOut,
    TemplateTestRequest,
    TemplateTestResult,
    TemplateUpdate,
)
from backend.services.template_runner import run_template_test

router = APIRouter(prefix="/templates", tags=["templates"])


# ------------------------------------------------------------------ helpers --

async def _with_count(template: PromptTemplate, db) -> TemplateOut:
    count = await db.scalar(
        select(func.count(Campaign.id)).where(Campaign.prompt_template_id == template.id)
    )
    out = TemplateOut.model_validate(template)
    out.campaigns_count = count or 0
    return out


# ------------------------------------------------------------------ routes ---

@router.get("", response_model=APIResponse[list[TemplateOut]])
async def list_templates(_: CurrentUser, db: DB):
    templates = (
        await db.execute(select(PromptTemplate).order_by(PromptTemplate.created_at.asc()))
    ).scalars().all()

    # Batch-fetch campaign counts in one query
    counts_rows = (
        await db.execute(
            select(Campaign.prompt_template_id, func.count(Campaign.id).label("n"))
            .where(Campaign.prompt_template_id.is_not(None))
            .group_by(Campaign.prompt_template_id)
        )
    ).all()
    counts_map = {row.prompt_template_id: row.n for row in counts_rows}

    result = []
    for t in templates:
        out = TemplateOut.model_validate(t)
        out.campaigns_count = counts_map.get(t.id, 0)
        result.append(out)

    return APIResponse.ok(result, f"{len(result)} templates")


@router.post("", response_model=APIResponse[TemplateOut], status_code=status.HTTP_201_CREATED)
async def create_template(body: TemplateCreate, _: CurrentUser, db: DB):
    template = PromptTemplate(**body.model_dump())
    db.add(template)
    await db.flush()
    await db.refresh(template)
    out = TemplateOut.model_validate(template)
    out.campaigns_count = 0
    return APIResponse.ok(out, "Template created")


@router.get("/{template_id}", response_model=APIResponse[TemplateOut])
async def get_template(template_id: uuid.UUID, _: CurrentUser, db: DB):
    template = await db.scalar(select(PromptTemplate).where(PromptTemplate.id == template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return APIResponse.ok(await _with_count(template, db))


@router.put("/{template_id}", response_model=APIResponse[TemplateOut])
async def update_template(template_id: uuid.UUID, body: TemplateUpdate, _: CurrentUser, db: DB):
    template = await db.scalar(select(PromptTemplate).where(PromptTemplate.id == template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(template, field, value)

    await db.flush()
    await db.refresh(template)
    return APIResponse.ok(await _with_count(template, db), "Template updated")


@router.delete("/{template_id}", response_model=APIResponse[None])
async def delete_template(template_id: uuid.UUID, _: CurrentUser, db: DB):
    template = await db.scalar(select(PromptTemplate).where(PromptTemplate.id == template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    in_use = await db.scalar(
        select(func.count(Campaign.id)).where(Campaign.prompt_template_id == template_id)
    )
    if in_use:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template is used by {in_use} campaign(s) — unassign them first",
        )

    await db.delete(template)
    await db.flush()
    return APIResponse.ok(None, "Template deleted")


@router.post("/{template_id}/test", response_model=APIResponse[TemplateTestResult])
async def test_template(template_id: uuid.UUID, body: TemplateTestRequest, _: CurrentUser, db: DB):
    template = await db.scalar(select(PromptTemplate).where(PromptTemplate.id == template_id))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    result = await run_template_test(
        template=template,
        test_keyword=body.test_keyword,
        campaign_id=body.campaign_id,
        db=db,
    )
    return APIResponse.ok(TemplateTestResult(**result), "Test complete")
