from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import CurrentUser, DB
from backend.models import Campaign, Project
from backend.schemas.common import APIResponse
from backend.schemas.cost import (
    CampaignCostOut,
    CostEstimateOut,
    CostEstimateRequest,
    DailyBreakdown,
    ProjectCostOut,
    ProjectCostSummary,
)
from backend.services.cost_calculator import (
    estimate_bulk_cost,
    get_all_projects_cost_this_month,
    get_campaign_cost,
    get_daily_breakdown,
    get_project_cost,
)

router = APIRouter(prefix="/costs", tags=["costs"])


def _parse_month(month_str: str | None) -> tuple[int, int]:
    """Parse 'YYYY-MM' string, default to current month."""
    if month_str:
        try:
            parts = month_str.split("-")
            return int(parts[0]), int(parts[1])
        except (IndexError, ValueError):
            raise HTTPException(status_code=422, detail="month must be YYYY-MM format")
    now = datetime.now(timezone.utc)
    return now.year, now.month


@router.get(
    "/project/{project_id}",
    response_model=APIResponse[ProjectCostOut],
)
async def project_cost(
    project_id: uuid.UUID,
    month: str | None = Query(None, description="YYYY-MM"),
    _: CurrentUser,
    db: DB,
):
    project = await db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    year, mon = _parse_month(month)
    cost_data = await get_project_cost(project_id, db, year=year, month=mon)
    daily = await get_daily_breakdown(db, project_id=project_id, year=year, month=mon)

    budget = Decimal(str(project.monthly_budget_usd or 0))
    total = cost_data["total_usd"]
    remaining = max(Decimal("0"), budget - total)
    pct_used = (
        ((total / budget) * 100).quantize(Decimal("0.01"))
        if budget > 0
        else Decimal("0")
    )

    return APIResponse.ok(
        data=ProjectCostOut(
            total_usd=total,
            pages_count=cost_data["pages_count"],
            tokens_input=cost_data["tokens_input"],
            tokens_output=cost_data["tokens_output"],
            budget_usd=budget,
            budget_remaining=remaining,
            budget_percent_used=pct_used,
            daily_breakdown=[DailyBreakdown(**d) for d in daily],
        ),
        message=f"Costs for {year}-{mon:02d}",
    )


@router.get(
    "/campaign/{campaign_id}",
    response_model=APIResponse[CampaignCostOut],
)
async def campaign_cost(
    campaign_id: uuid.UUID,
    month: str | None = Query(None, description="YYYY-MM"),
    _: CurrentUser,
    db: DB,
):
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    year, mon = _parse_month(month)
    cost_data = await get_campaign_cost(campaign_id, db, year=year, month=mon)
    daily = await get_daily_breakdown(db, campaign_id=campaign_id, year=year, month=mon)

    return APIResponse.ok(
        data=CampaignCostOut(
            total_usd=cost_data["total_usd"],
            pages_count=cost_data["pages_count"],
            tokens_input=cost_data["tokens_input"],
            tokens_output=cost_data["tokens_output"],
            daily_breakdown=[DailyBreakdown(**d) for d in daily],
        ),
        message=f"Costs for {year}-{mon:02d}",
    )


@router.post(
    "/estimate",
    response_model=APIResponse[CostEstimateOut],
)
async def cost_estimate(
    body: CostEstimateRequest,
    _: CurrentUser,
    db: DB,
):
    campaign = await db.scalar(select(Campaign).where(Campaign.id == body.campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    model = campaign.model or "claude-sonnet-4-20250514"
    est = estimate_bulk_cost(body.keyword_count, model)

    return APIResponse.ok(
        data=CostEstimateOut(
            model=model,
            keyword_count=body.keyword_count,
            **est,
        ),
        message="Estimate calculated",
    )


@router.get(
    "/summary",
    response_model=APIResponse[list[ProjectCostSummary]],
)
async def cost_summary(
    _: CurrentUser,
    db: DB,
):
    rows = await get_all_projects_cost_this_month(db)
    return APIResponse.ok(
        data=[ProjectCostSummary(**r) for r in rows],
        message=f"{len(rows)} projects",
    )
