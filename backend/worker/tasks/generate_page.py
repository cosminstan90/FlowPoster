"""
ARQ task: run the AI generation pipeline for a single keyword.

Handles all exceptions — the keyword is always left in a coherent state
(either ``draft`` on success or ``error`` with a message on failure).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models import Keyword

logger = logging.getLogger(__name__)


async def run_generation_pipeline(ctx: dict, keyword_id_str: str) -> None:
    # Lazy import to avoid circular dependency at worker import time
    from backend.services.ai.pipeline import run_pipeline

    keyword_id = uuid.UUID(keyword_id_str)
    logger.info("Worker starting pipeline for keyword %s", keyword_id)

    async with AsyncSessionLocal() as db:
        try:
            page = await run_pipeline(keyword_id, db)
            await db.commit()
            logger.info(
                "Worker completed keyword %s → page %s (score=%d, cost=$%s)",
                keyword_id,
                page.id,
                page.quality_score,
                page.cost_usd,
            )
            from backend.services.telegram_service import send_telegram
            kw_obj = await db.scalar(select(Keyword).where(Keyword.id == keyword_id))
            kw_text = kw_obj.keyword if kw_obj else str(keyword_id)
            await send_telegram(
                f"✅ <b>Pagină generată</b>\n"
                f"Keyword: <code>{kw_text}</code>\n"
                f"Score: {page.quality_score} · Cost: ${page.cost_usd}"
            )
        except Exception as exc:
            await db.rollback()
            logger.exception("Worker pipeline failed for keyword %s", keyword_id)

            # Ensure the keyword is marked as error even if pipeline.py
            # didn't manage to do so (e.g. connectivity loss mid-way).
            async with AsyncSessionLocal() as err_db:
                try:
                    kw = await err_db.scalar(
                        select(Keyword).where(Keyword.id == keyword_id)
                    )
                    if kw and kw.status != "error":
                        kw.status = "error"
                        kw.error_message = str(exc)[:2000]
                        kw.updated_at = datetime.now(timezone.utc)
                        await err_db.commit()

                    from backend.services.telegram_service import send_telegram
                    kw_text = kw.keyword if kw else str(keyword_id)
                    await send_telegram(
                        f"❌ <b>Generare eșuată</b>\n"
                        f"Keyword: <code>{kw_text}</code>\n"
                        f"Eroare: {str(exc)[:300]}"
                    )
                except Exception:
                    logger.exception(
                        "Failed to set error status on keyword %s", keyword_id
                    )
