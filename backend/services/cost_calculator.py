"""
Cost tracking and estimation for AI generation usage.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import cast, extract, func, select, Date
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Campaign, GeneratedPage, Keyword, Project
from backend.services.ai.claude_client import _PRICING, _DEFAULT_INPUT, _DEFAULT_OUTPUT


# ------------------------------------------------------------------
# Pure calculation
# ------------------------------------------------------------------

def calculate_page_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
) -> Decimal:
    """Return the USD cost for a single page given its token counts."""
    price_in, price_out = _PRICING.get(model, (_DEFAULT_INPUT, _DEFAULT_OUTPUT))
    return price_in * input_tokens + price_out * output_tokens


# ------------------------------------------------------------------
# DB aggregation helpers
# ------------------------------------------------------------------

def _base_pages_query(
    *,
    project_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    year: int | None = None,
    month: int | None = None,
):
    """Build a select over GeneratedPage with optional project/campaign/month filters."""
    q = select(GeneratedPage)

    if project_id is not None or campaign_id is not None:
        q = q.join(Keyword, Keyword.id == GeneratedPage.keyword_id)

    if project_id is not None:
        q = q.join(Campaign, Campaign.id == Keyword.campaign_id).where(
            Campaign.project_id == project_id
        )
    elif campaign_id is not None:
        q = q.where(Keyword.campaign_id == campaign_id)

    if year is not None and month is not None:
        q = q.where(
            extract("year", GeneratedPage.created_at) == year,
            extract("month", GeneratedPage.created_at) == month,
        )

    return q


async def get_project_cost(
    project_id: uuid.UUID,
    db: AsyncSession,
    year: int | None = None,
    month: int | None = None,
) -> dict:
    """
    Aggregate cost data for a project, optionally filtered by month.

    Returns::

        {
            "total_usd": Decimal,
            "pages_count": int,
            "tokens_input": int,
            "tokens_output": int,
        }
    """
    base = _base_pages_query(project_id=project_id, year=year, month=month)

    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(GeneratedPage.cost_usd), 0).label("total_usd"),
                func.count(GeneratedPage.id).label("pages_count"),
                func.coalesce(func.sum(GeneratedPage.input_tokens), 0).label("tokens_input"),
                func.coalesce(func.sum(GeneratedPage.output_tokens), 0).label("tokens_output"),
            ).select_from(base.subquery())
        )
    ).one()

    return {
        "total_usd": Decimal(str(row.total_usd)),
        "pages_count": row.pages_count,
        "tokens_input": row.tokens_input,
        "tokens_output": row.tokens_output,
    }


async def get_campaign_cost(
    campaign_id: uuid.UUID,
    db: AsyncSession,
    year: int | None = None,
    month: int | None = None,
) -> dict:
    """Same shape as get_project_cost but scoped to one campaign."""
    base = _base_pages_query(campaign_id=campaign_id, year=year, month=month)

    row = (
        await db.execute(
            select(
                func.coalesce(func.sum(GeneratedPage.cost_usd), 0).label("total_usd"),
                func.count(GeneratedPage.id).label("pages_count"),
                func.coalesce(func.sum(GeneratedPage.input_tokens), 0).label("tokens_input"),
                func.coalesce(func.sum(GeneratedPage.output_tokens), 0).label("tokens_output"),
            ).select_from(base.subquery())
        )
    ).one()

    return {
        "total_usd": Decimal(str(row.total_usd)),
        "pages_count": row.pages_count,
        "tokens_input": row.tokens_input,
        "tokens_output": row.tokens_output,
    }


async def get_daily_breakdown(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    year: int,
    month: int,
) -> list[dict]:
    """
    Daily cost breakdown for a month.

    Returns list of ``{"date": "YYYY-MM-DD", "cost": Decimal, "pages": int}``.
    """
    base = _base_pages_query(
        project_id=project_id,
        campaign_id=campaign_id,
        year=year,
        month=month,
    )
    sub = base.subquery()

    rows = (
        await db.execute(
            select(
                cast(sub.c.created_at, Date).label("day"),
                func.coalesce(func.sum(sub.c.cost_usd), 0).label("cost"),
                func.count(sub.c.id).label("pages"),
            )
            .group_by("day")
            .order_by("day")
        )
    ).all()

    return [
        {
            "date": str(r.day),
            "cost": Decimal(str(r.cost)),
            "pages": r.pages,
        }
        for r in rows
    ]


def estimate_bulk_cost(
    keyword_count: int,
    model: str,
    avg_tokens_per_page: int = 4000,
) -> dict:
    """
    Quick cost estimate for a bulk generation run.

    The pipeline makes ~6 API calls per keyword. We estimate:
    - Input tokens  ≈ avg_tokens_per_page * 1.5  (prompts + context)
    - Output tokens ≈ avg_tokens_per_page         (generated content)

    Returns ``{"min_usd": Decimal, "max_usd": Decimal, "estimated_tokens": int}``.
    """
    price_in, price_out = _PRICING.get(model, (_DEFAULT_INPUT, _DEFAULT_OUTPUT))

    est_input = int(avg_tokens_per_page * 1.5)
    est_output = avg_tokens_per_page
    est_total_tokens = (est_input + est_output) * keyword_count

    cost_per_page = price_in * est_input + price_out * est_output
    mid = cost_per_page * keyword_count

    return {
        "min_usd": (mid * Decimal("0.7")).quantize(Decimal("0.000001")),
        "max_usd": (mid * Decimal("1.4")).quantize(Decimal("0.000001")),
        "estimated_tokens": est_total_tokens,
    }


async def get_all_projects_cost_this_month(db: AsyncSession) -> list[dict]:
    """
    Summary for every project in the current month, sorted by cost desc.

    Returns list of::

        {"project_id": UUID, "project_name": str, "total_usd": Decimal,
         "pages_count": int, "tokens_input": int, "tokens_output": int}
    """
    now = datetime.now(timezone.utc)

    rows = (
        await db.execute(
            select(
                Project.id.label("project_id"),
                Project.name.label("project_name"),
                Project.monthly_budget_usd.label("budget_usd"),
                Project.budget_alert_level.label("budget_alert_level"),
                func.coalesce(func.sum(GeneratedPage.cost_usd), 0).label("total_usd"),
                func.count(GeneratedPage.id).label("pages_count"),
                func.coalesce(func.sum(GeneratedPage.input_tokens), 0).label("tokens_input"),
                func.coalesce(func.sum(GeneratedPage.output_tokens), 0).label("tokens_output"),
            )
            .outerjoin(Campaign, Campaign.project_id == Project.id)
            .outerjoin(Keyword, Keyword.campaign_id == Campaign.id)
            .outerjoin(
                GeneratedPage,
                (GeneratedPage.keyword_id == Keyword.id)
                & (extract("year", GeneratedPage.created_at) == now.year)
                & (extract("month", GeneratedPage.created_at) == now.month),
            )
            .group_by(Project.id, Project.name, Project.monthly_budget_usd, Project.budget_alert_level)
            .order_by(func.sum(GeneratedPage.cost_usd).desc().nulls_last())
        )
    ).all()

    result = []
    for r in rows:
        total = Decimal(str(r.total_usd))
        budget = Decimal(str(r.budget_usd or 0))
        pct = (
            ((total / budget) * 100).quantize(Decimal("0.01"))
            if budget > 0
            else Decimal("0")
        )
        result.append({
            "project_id": r.project_id,
            "project_name": r.project_name,
            "total_usd": total,
            "pages_count": r.pages_count,
            "tokens_input": r.tokens_input,
            "tokens_output": r.tokens_output,
            "budget_usd": budget,
            "budget_percent_used": pct,
            "budget_alert_level": r.budget_alert_level or "none",
        })
    return result
