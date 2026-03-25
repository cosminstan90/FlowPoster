"""GEO performance report endpoint."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import CurrentUser, DB
from backend.models import Campaign, GeneratedPage, Keyword, Project
from backend.schemas.common import APIResponse

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/report", response_model=APIResponse[list[dict]])
async def geo_report(_: CurrentUser, db: DB):
    """
    Return GEO performance stats for all geo-enabled campaigns.
    """
    # Get all geo-enabled campaigns
    campaigns = (
        await db.execute(
            select(Campaign).where(Campaign.geo_enabled == True)
        )
    ).scalars().all()

    result = []
    for campaign in campaigns:
        # Count pages with geo score
        pages = (
            await db.execute(
                select(GeneratedPage)
                .join(Keyword, Keyword.id == GeneratedPage.keyword_id)
                .where(
                    Keyword.campaign_id == campaign.id,
                    GeneratedPage.geo_score.is_not(None),
                )
            )
        ).scalars().all()

        if not pages:
            result.append({
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "geo_mode": campaign.geo_mode,
                "pages_with_geo": 0,
                "avg_geo_score": None,
                "score_distribution": {"low": 0, "mid": 0, "high": 0},
                "failing_factors": {},
            })
            continue

        scores = [p.geo_score for p in pages]
        avg_score = round(sum(scores) / len(scores), 1)

        distribution = {
            "low": sum(1 for s in scores if s <= 40),
            "mid": sum(1 for s in scores if 41 <= s <= 70),
            "high": sum(1 for s in scores if s > 70),
        }

        # Aggregate failing factors across all pages
        factor_fails: dict[str, int] = {}
        for page in pages:
            if not page.geo_breakdown:
                continue
            for factor, val in page.geo_breakdown.items():
                if not val.get("ok", True):
                    factor_fails[factor] = factor_fails.get(factor, 0) + 1

        result.append({
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.name,
            "geo_mode": campaign.geo_mode,
            "pages_with_geo": len(pages),
            "avg_geo_score": avg_score,
            "score_distribution": distribution,
            "failing_factors": factor_fails,
        })

    return APIResponse.ok(data=result, message=f"{len(result)} geo-enabled campaigns")
