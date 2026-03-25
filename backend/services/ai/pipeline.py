"""
AI generation pipeline — orchestrates all 8 steps for a single keyword.

Returns a persisted GeneratedPage or raises on unrecoverable error.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Campaign, GeneratedPage, Keyword, SiteContext
from backend.services.ai.claude_client import CallResult, ClaudeClient
from backend.services.ai import prompts
from backend.services.ai.quality_scorer import score as quality_score
from backend.services.budget_checker import check_and_update_budget_alert
from backend.services.duplicate_guard import DuplicateGuard

logger = logging.getLogger(__name__)

HAIKU = "claude-haiku-4-5-20251001"

# GEO version constant (imported lazily but defined here to avoid NameError)
try:
    from backend.services.ai.geo_generator import GEO_VERSION
except ImportError:
    GEO_VERSION = "1.0"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

class _TokenAccumulator:
    """Collects token counts and costs across all pipeline steps."""

    def __init__(self) -> None:
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.cost_usd: Decimal = Decimal("0")

    def add(self, result: CallResult) -> None:
        self.input_tokens += result.input_tokens
        self.output_tokens += result.output_tokens
        self.cost_usd += result.cost_usd


def _parse_json(text: str) -> dict:
    """Extract and parse JSON from LLM output that may contain markdown fences."""
    cleaned = text.strip()
    # strip markdown code fences
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(1).strip()
    return json.loads(cleaned)


def _first_n_words(html: str, n: int) -> str:
    """Return the first *n* words from HTML, tags stripped."""
    plain = re.sub(r"<[^>]+>", " ", html)
    words = plain.split()
    return " ".join(words[:n])


async def _set_error(kw: Keyword, msg: str, db: AsyncSession) -> None:
    kw.status = "error"
    kw.error_message = msg
    kw.updated_at = datetime.now(timezone.utc)
    await db.flush()


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

async def run_pipeline(keyword_id: uuid.UUID, db: AsyncSession) -> GeneratedPage:
    """
    Execute the full 8-step generation pipeline for a single keyword.

    The caller is responsible for committing the session.
    """

    # ---- Load entities ------------------------------------------------
    kw = await db.scalar(select(Keyword).where(Keyword.id == keyword_id))
    if not kw:
        raise ValueError(f"Keyword {keyword_id} not found")

    campaign = await db.scalar(select(Campaign).where(Campaign.id == kw.campaign_id))
    if not campaign:
        raise ValueError(f"Campaign {kw.campaign_id} not found")

    site_ctx = await db.scalar(
        select(SiteContext).where(SiteContext.project_id == campaign.project_id)
    )
    if not site_ctx:
        await _set_error(kw, "SiteContext not configured for this project", db)
        raise ValueError("SiteContext missing")

    # Mark keyword as generating
    kw.status = "generating"
    kw.updated_at = datetime.now(timezone.utc)
    await db.flush()

    campaign_model = campaign.model or "claude-sonnet-4-20250514"
    haiku_client = ClaudeClient(HAIKU)
    campaign_client = ClaudeClient(campaign_model)
    tokens = _TokenAccumulator()

    language = campaign.language or "ro"

    try:
        # =============================================================
        # Step 1 — Intent Detector  (haiku)
        # =============================================================
        sys_p, usr_p = prompts.intent_detector(kw.keyword, site_ctx.niche)
        intent_result = await haiku_client.call(sys_p, usr_p, max_tokens=256)
        tokens.add(intent_result)

        intent_data = _parse_json(intent_result.text)
        search_intent = intent_data.get("search_intent", "informational")
        page_type = intent_data.get("page_type", "blog_post")

        # persist on the keyword
        kw.search_intent = search_intent[:50]
        kw.page_type = page_type[:50]

        # =============================================================
        # Step 2 — Duplicate Guard
        # =============================================================
        guard = await DuplicateGuard.build(kw.campaign_id, db)
        dup_check = guard.check(kw.keyword)
        if dup_check.is_duplicate:
            await _set_error(kw, "Duplicate keyword detected (similarity > 85%)", db)
            raise ValueError(f"Keyword '{kw.keyword}' is a duplicate")

        # =============================================================
        # Step 3 — Outline Generator  (campaign model)
        # =============================================================
        sys_p, usr_p = prompts.outline_generator(
            keyword=kw.keyword,
            search_intent=search_intent,
            niche=site_ctx.niche,
            target_audience=site_ctx.target_audience,
            tone=site_ctx.tone,
            language=language,
        )
        outline_result = await campaign_client.call(sys_p, usr_p, max_tokens=2048)
        tokens.add(outline_result)

        outline_data = _parse_json(outline_result.text)
        faq_questions: list[str] = outline_data.get("faq_questions", [])

        # =============================================================
        # Step 4 — Content Generator  (campaign model OR GEO generator)
        # =============================================================
        # Gather existing slugs for internal linking
        slug_rows = await db.execute(
            select(GeneratedPage.slug)
            .join(Keyword, Keyword.id == GeneratedPage.keyword_id)
            .join(Campaign, Campaign.id == Keyword.campaign_id)
            .where(Campaign.project_id == campaign.project_id)
            .where(GeneratedPage.slug.is_not(None))
        )
        existing_slugs = [r[0] for r in slug_rows.all()]

        internal_links: list[dict] = []
        geo_direct_answer = ""
        geo_speakable_sections: list[str] = []
        geo_has_comparison_table = False

        if getattr(campaign, 'geo_enabled', False):
            from backend.services.ai.geo_generator import generate_geo_content, GEO_VERSION
            geo_result = await generate_geo_content(
                keyword=kw.keyword,
                search_intent=search_intent,
                outline_json=outline_result.text,
                niche=site_ctx.niche,
                target_audience=site_ctx.target_audience,
                tone=site_ctx.tone,
                topics_to_avoid=site_ctx.topics_to_avoid or "",
                author_name=site_ctx.author_name or "",
                author_bio=site_ctx.author_bio or "",
                author_credentials=site_ctx.author_credentials or "",
                existing_slugs=existing_slugs,
                language=language,
                geo_mode=getattr(campaign, 'geo_mode', 'balanced'),
                model=campaign_model,
            )
            tokens.add(geo_result.call_result)
            content_html: str = geo_result.content_html
            internal_links = []  # will be extracted from GEO result if needed
            geo_direct_answer = geo_result.direct_answer
            geo_speakable_sections = geo_result.speakable_sections
            geo_has_comparison_table = geo_result.has_comparison_table
        else:
            sys_p, usr_p = prompts.content_generator(
                keyword=kw.keyword,
                outline_json=outline_result.text,
                niche=site_ctx.niche,
                target_audience=site_ctx.target_audience,
                tone=site_ctx.tone,
                topics_to_avoid=site_ctx.topics_to_avoid,
                author_name=site_ctx.author_name,
                author_bio=site_ctx.author_bio,
                author_credentials=site_ctx.author_credentials,
                existing_slugs=existing_slugs,
                language=language,
            )
            content_result = await campaign_client.call(sys_p, usr_p, max_tokens=8192)
            tokens.add(content_result)

            content_data = _parse_json(content_result.text)
            content_html: str = content_data.get("content_html", "")
            internal_links = content_data.get("internal_links_used", [])

        # =============================================================
        # Step 5 — SEO Layer  (haiku)
        # =============================================================
        sys_p, usr_p = prompts.seo_layer(content_html, kw.keyword, language)
        seo_result = await haiku_client.call(sys_p, usr_p, max_tokens=512)
        tokens.add(seo_result)

        seo_data = _parse_json(seo_result.text)
        title = seo_data.get("title", "")[:500]
        meta_description = seo_data.get("meta_description", "")[:500]
        slug = seo_data.get("slug", "")[:500]

        # =============================================================
        # Step 6 — Schema Generator  (haiku)
        # =============================================================
        # Extract FAQ answers from content for richer schema
        sys_p, usr_p = prompts.schema_generator(
            title=title,
            content_snippet=_first_n_words(content_html, 150),
            faq_questions=faq_questions,
            faq_html=content_html,
        )
        schema_result = await haiku_client.call(sys_p, usr_p, max_tokens=2048)
        tokens.add(schema_result)

        schema_markup: dict | None = None
        try:
            schema_markup = _parse_json(schema_result.text)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Schema generation returned invalid JSON, storing as null")

        # GEO Schema enhancement
        if getattr(campaign, 'geo_enabled', False):
            from backend.services.ai.geo_schema import build_geo_schema
            is_howto = kw.keyword.lower().startswith(("cum ", "how ", "cum să", "how to", "cum se"))
            is_concept = search_intent == "informational" and not is_howto
            schema_markup = build_geo_schema(
                existing_schema=schema_markup,
                title=title,
                keyword=kw.keyword,
                content_html=content_html,
                speakable_sections=geo_speakable_sections,
                faq_items=[],
                is_howto=is_howto,
                is_concept=is_concept,
                has_qa=len(faq_questions) >= 3,
            )

        # =============================================================
        # Step 7 — Intent Validator  (haiku)
        # =============================================================
        content_start = _first_n_words(content_html, 300)
        sys_p, usr_p = prompts.intent_validator(kw.keyword, search_intent, content_start)
        validator_result = await haiku_client.call(sys_p, usr_p, max_tokens=512)
        tokens.add(validator_result)

        validator_data = _parse_json(validator_result.text)
        intent_passes: bool = validator_data.get("passes", True)
        intent_issues: list[str] = validator_data.get("issues", [])

        # =============================================================
        # Step 8 — Quality Scorer  (pure Python)
        # =============================================================
        quality = quality_score(
            content_html=content_html,
            title=title,
            keyword=kw.keyword,
            faq_items=faq_questions,
            schema_markup=schema_markup,
            meta_description=meta_description,
        )

        # GEO Scoring
        geo_score_val = None
        geo_breakdown = None
        geo_citation_density = None
        if getattr(campaign, 'geo_enabled', False):
            from backend.services.geo_scorer import score_geo
            geo = score_geo(
                content_html=content_html,
                keyword=kw.keyword,
                direct_answer=geo_direct_answer,
                speakable_sections=geo_speakable_sections,
                has_comparison_table=geo_has_comparison_table,
                schema_markup=schema_markup,
                faq_items=[{"question": q} for q in faq_questions],
                author_name=site_ctx.author_name,
            )
            geo_score_val = geo.score
            geo_breakdown = geo.breakdown
            geo_citation_density = geo.citation_density

        # =============================================================
        # Persist GeneratedPage
        # =============================================================
        faq_items = [{"question": q} for q in faq_questions]

        page = GeneratedPage(
            keyword_id=kw.id,
            title=title,
            slug=slug,
            meta_description=meta_description,
            content_html=content_html,
            schema_markup=schema_markup,
            faq_items=faq_items,
            internal_links_suggested=internal_links,
            word_count=quality.word_count,
            quality_score=quality.score,
            readability_score=quality.readability_score,
            intent_validation_passed=intent_passes,
            intent_validation_issues=intent_issues,
            input_tokens=tokens.input_tokens,
            output_tokens=tokens.output_tokens,
            model_used=campaign_model,
            cost_usd=tokens.cost_usd,
            geo_score=geo_score_val,
            geo_breakdown=geo_breakdown,
            speakable_sections=geo_speakable_sections if getattr(campaign, 'geo_enabled', False) else None,
            geo_version=GEO_VERSION if getattr(campaign, 'geo_enabled', False) else None,
            has_direct_answer=bool(geo_direct_answer),
            has_comparison_table=geo_has_comparison_table,
            citation_density=geo_citation_density,
        )
        db.add(page)

        kw.status = "draft"
        kw.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(page)

        # Budget alert check (best-effort — never fail the pipeline)
        try:
            await check_and_update_budget_alert(campaign.project_id, db)
        except Exception:
            logger.warning("Budget alert check failed for project %s", campaign.project_id)

        logger.info(
            "Pipeline complete for keyword=%s | score=%d | tokens_in=%d tokens_out=%d cost=$%s",
            kw.keyword,
            quality.score,
            tokens.input_tokens,
            tokens.output_tokens,
            tokens.cost_usd,
        )
        return page

    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        msg = f"Pipeline JSON parsing error: {exc}"
        logger.error(msg)
        await _set_error(kw, msg, db)
        raise ValueError(msg) from exc
    except ValueError:
        # Already handled (duplicate guard, missing entities)
        raise
    except Exception as exc:
        msg = f"Pipeline error: {exc}"
        logger.error(msg, exc_info=True)
        await _set_error(kw, msg, db)
        raise
