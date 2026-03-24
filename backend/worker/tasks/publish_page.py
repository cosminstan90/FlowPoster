"""
ARQ task: publish a GeneratedPage to the project's CMS using the publish adapters.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database import AsyncSessionLocal
from backend.models.campaign import Campaign
from backend.models.generated_page import GeneratedPage
from backend.models.keyword import Keyword
from backend.models.project import Project
from backend.services.cms import get_adapter

logger = logging.getLogger(__name__)


async def publish_page(ctx: dict, page_id_str: str) -> None:
    page_id = uuid.UUID(page_id_str)
    logger.info("Worker starting publish for page %s", page_id)

    async with AsyncSessionLocal() as db:
        try:
            page = await db.scalar(
                select(GeneratedPage)
                .where(GeneratedPage.id == page_id)
                .options(selectinload(GeneratedPage.keyword).selectinload(Keyword.campaign))
            )
            if not page:
                logger.error("Page %s not found", page_id)
                return

            if page.status not in ("draft", "approved"):
                logger.warning(
                    "Page %s has status '%s', expected draft/approved — skipping",
                    page_id, page.status,
                )
                return

            campaign: Campaign = page.keyword.campaign
            project: Project = await db.scalar(
                select(Project).where(Project.id == campaign.project_id)
            )
            if not project:
                logger.error("Project not found for page %s", page_id)
                return

            adapter = get_adapter(project)
            result = await adapter.publish(page)

            if not result["success"]:
                logger.error("CMS adapter returned failure for page %s", page_id)
                return

            page.status = "published"
            page.published_url = result["published_url"]
            page.published_at = datetime.now(timezone.utc)

            keyword: Keyword = page.keyword
            keyword.status = "published"
            keyword.updated_at = datetime.now(timezone.utc)

            await db.commit()
            logger.info("Published page %s → %s", page_id, result["published_url"])

        except Exception as exc:
            await db.rollback()
            logger.exception("Publish failed for page %s: %s", page_id, exc)
