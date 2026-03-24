"""
Budget alert checker — runs after every GeneratedPage is saved.

Computes cost_this_month for the project and updates
project.budget_alert_level: 'none' | 'warning' (≥80%) | 'critical' (≥95%).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Campaign, GeneratedPage, Keyword, Project

_WARNING_THRESHOLD = Decimal("0.80")
_CRITICAL_THRESHOLD = Decimal("0.95")


async def check_and_update_budget_alert(
    project_id: uuid.UUID,
    db: AsyncSession,
) -> str:
    """
    Recalculate this-month spend for *project_id*, update
    ``project.budget_alert_level``, and flush.

    Returns the new alert level string.
    """
    now = datetime.now(timezone.utc)

    project = await db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        return "none"

    budget = Decimal(str(project.monthly_budget_usd or 0))
    if budget <= 0:
        # No budget set — nothing to alert on
        if project.budget_alert_level != "none":
            project.budget_alert_level = "none"
            await db.flush()
        return "none"

    # Sum cost_usd for all pages in this project this month
    total_row = await db.execute(
        select(func.coalesce(func.sum(GeneratedPage.cost_usd), 0).label("total"))
        .join(Keyword, Keyword.id == GeneratedPage.keyword_id)
        .join(Campaign, Campaign.id == Keyword.campaign_id)
        .where(
            Campaign.project_id == project_id,
            extract("year", GeneratedPage.created_at) == now.year,
            extract("month", GeneratedPage.created_at) == now.month,
        )
    )
    total_usd = Decimal(str(total_row.scalar_one()))

    pct = total_usd / budget

    if pct >= _CRITICAL_THRESHOLD:
        level = "critical"
    elif pct >= _WARNING_THRESHOLD:
        level = "warning"
    else:
        level = "none"

    if project.budget_alert_level != level:
        project.budget_alert_level = level
        await db.flush()

    return level
