import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import CurrentUser, DB
from backend.models import Campaign, Keyword, Project
from backend.schemas.campaign import (
    CampaignCreate,
    CampaignDetail,
    CampaignOut,
    CampaignUpdate,
    KeywordCounts,
)
from backend.schemas.common import APIResponse

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _counts_query(campaign_id: uuid.UUID):
    return (
        select(
            Campaign,
            func.count(Keyword.id).label("total"),
            func.count(case((Keyword.status == "pending", Keyword.id))).label("pending"),
            func.count(case((Keyword.status == "queued", Keyword.id))).label("queued"),
            func.count(case((Keyword.status == "generating", Keyword.id))).label("generating"),
            func.count(case((Keyword.status == "draft", Keyword.id))).label("draft"),
            func.count(case((Keyword.status == "approved", Keyword.id))).label("approved"),
            func.count(case((Keyword.status == "published", Keyword.id))).label("published"),
            func.count(case((Keyword.status == "error", Keyword.id))).label("error"),
        )
        .outerjoin(Keyword, Keyword.campaign_id == Campaign.id)
        .where(Campaign.id == campaign_id)
        .group_by(Campaign.id)
    )


def _row_to_detail(row) -> CampaignDetail:
    out = CampaignDetail.model_validate(row.Campaign)
    out.keyword_counts = KeywordCounts(
        total=row.total or 0,
        pending=row.pending or 0,
        queued=row.queued or 0,
        generating=row.generating or 0,
        draft=row.draft or 0,
        approved=row.approved or 0,
        published=row.published or 0,
        error=row.error or 0,
    )
    return out


@router.get("", response_model=APIResponse[list[CampaignOut]])
async def list_campaigns(
    project_id: uuid.UUID | None = None,
    _: str = CurrentUser,
    db: DB,
):
    stmt = select(Campaign).order_by(Campaign.created_at.desc())
    if project_id is not None:
        stmt = stmt.where(Campaign.project_id == project_id)
    result = await db.execute(stmt)
    campaigns = result.scalars().all()
    data = [CampaignOut.model_validate(c) for c in campaigns]
    return APIResponse.ok(data=data, message=f"{len(data)} campaigns")


@router.post("", response_model=APIResponse[CampaignOut], status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    _: str = CurrentUser,
    db: DB,
):
    project_exists = await db.scalar(select(Project.id).where(Project.id == body.project_id))
    if not project_exists:
        raise HTTPException(status_code=404, detail="Project not found")

    payload = body.model_dump()
    campaign = Campaign(**payload)
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return APIResponse.ok(data=CampaignOut.model_validate(campaign), message="Campaign created")


@router.get("/{campaign_id}", response_model=APIResponse[CampaignDetail])
async def get_campaign(
    campaign_id: uuid.UUID,
    _: str = CurrentUser,
    db: DB,
):
    result = await db.execute(_counts_query(campaign_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return APIResponse.ok(data=_row_to_detail(row), message="OK")


@router.put("/{campaign_id}", response_model=APIResponse[CampaignOut])
async def update_campaign(
    campaign_id: uuid.UUID,
    body: CampaignUpdate,
    _: str = CurrentUser,
    db: DB,
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "publish_schedule" and value is not None:
            value = value if isinstance(value, dict) else value.model_dump()
        setattr(campaign, field, value)

    await db.flush()
    await db.refresh(campaign)
    return APIResponse.ok(data=CampaignOut.model_validate(campaign), message="Campaign updated")


@router.delete("/{campaign_id}", response_model=APIResponse[None])
async def delete_campaign(
    campaign_id: uuid.UUID,
    _: str = CurrentUser,
    db: DB,
):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    keyword_count = await db.scalar(
        select(func.count(Keyword.id)).where(Keyword.campaign_id == campaign_id)
    )
    if keyword_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete campaign with {keyword_count} existing keyword(s)",
        )

    await db.delete(campaign)
    return APIResponse.ok(data=None, message="Campaign deleted")
