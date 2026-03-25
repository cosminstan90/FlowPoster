"""
ARQ cron task: scheduled automatic publishing.

Runs every hour. For each active campaign with publish_schedule enabled,
checks if the current UTC hour matches time_of_day, counts how many pages
were already published today, and enqueues publish jobs for the remainder.

publish_schedule JSON schema:
    {
        "enabled": true,
        "pages_per_day": 5,
        "time_of_day": "10:00"   # UTC HH:MM
    }
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import and_, extract, func, select

from backend.database import AsyncSessionLocal
from backend.models import Campaign, GeneratedPage, Keyword
from backend.worker.queue import get_arq_pool

logger = logging.getLogger(__name__)


async def scheduled_publish(ctx: dict) -> None:
    now = datetime.now(timezone.utc)
    current_hour = now.hour

    logger.info("scheduled_publish cron fired at UTC %02d:00", current_hour)

    async with AsyncSessionLocal() as db:
        # Load active campaigns that have a non-null publish_schedule
        campaigns = (
            await db.execute(
                select(Campaign).where(
                    Campaign.status == "active",
                    Campaign.publish_schedule.is_not(None),
                )
            )
        ).scalars().all()

        pool = await get_arq_pool()
        total_enqueued = 0

        for campaign in campaigns:
            schedule = campaign.publish_schedule or {}
            if not schedule.get("enabled"):
                continue

            pages_per_day: int = int(schedule.get("pages_per_day", 1))
            time_of_day: str = schedule.get("time_of_day", "00:00")

            try:
                scheduled_hour = int(time_of_day.split(":")[0])
            except (ValueError, IndexError):
                logger.warning(
                    "Campaign %s has invalid time_of_day '%s', skipping",
                    campaign.id, time_of_day,
                )
                continue

            if scheduled_hour != current_hour:
                continue

            # Count pages already published today for this campaign
            published_today: int = (
                await db.execute(
                    select(func.count(GeneratedPage.id))
                    .join(Keyword, Keyword.id == GeneratedPage.keyword_id)
                    .where(
                        Keyword.campaign_id == campaign.id,
                        GeneratedPage.status == "published",
                        extract("year", GeneratedPage.published_at) == now.year,
                        extract("month", GeneratedPage.published_at) == now.month,
                        extract("day", GeneratedPage.published_at) == now.day,
                    )
                )
            ).scalar_one()

            remaining = pages_per_day - published_today
            if remaining <= 0:
                logger.info(
                    "Campaign %s already published %d/%d pages today",
                    campaign.id, published_today, pages_per_day,
                )
                continue

            # Pick next approved pages (oldest first)
            approved_pages = (
                await db.execute(
                    select(GeneratedPage)
                    .join(Keyword, Keyword.id == GeneratedPage.keyword_id)
                    .where(
                        Keyword.campaign_id == campaign.id,
                        GeneratedPage.status == "approved",
                    )
                    .order_by(GeneratedPage.created_at.asc())
                    .limit(remaining)
                )
            ).scalars().all()

            for page in approved_pages:
                await pool.enqueue_job("publish_page", str(page.id))
                total_enqueued += 1
                logger.info(
                    "Scheduled publish enqueued page %s for campaign %s",
                    page.id, campaign.id,
                )

        logger.info(
            "scheduled_publish complete: %d jobs enqueued across %d campaigns",
            total_enqueued, len(campaigns),
        )
        if total_enqueued > 0:
            from backend.services.telegram_service import send_telegram
            await send_telegram(
                f"📅 <b>Publicare programată</b>\n"
                f"{total_enqueued} pagini trimise la publicare"
            )
