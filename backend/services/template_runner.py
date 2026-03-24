"""
Test-runner for prompt templates.

Executes Step 3 (outline, standard) + Step 4 (content, using the template's
system/user prompts with variable substitution) and returns a preview result.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Campaign, GeneratedPage, Keyword, SiteContext
from backend.models.prompt_template import PromptTemplate
from backend.services.ai.claude_client import ClaudeClient
from backend.services.ai.prompts import outline_generator

HAIKU = "claude-haiku-4-5-20251001"
_MAX_PREVIEW = 2000  # chars


def _parse_json_safe(text: str) -> dict:
    cleaned = text.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


def _substitute(template_str: str, variables: dict[str, str]) -> str:
    """Replace {var} placeholders with actual values."""
    for key, value in variables.items():
        template_str = template_str.replace(f"{{{key}}}", value)
    return template_str


async def run_template_test(
    template: PromptTemplate,
    test_keyword: str,
    campaign_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """
    Returns::

        {
            "content_preview": str,
            "tokens_used": int,
            "cost_usd": float,
            "time_seconds": float,
        }
    """
    t0 = time.perf_counter()

    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    site_ctx = await db.scalar(
        select(SiteContext).where(SiteContext.project_id == campaign.project_id)
    )

    language = campaign.language or "ro"
    campaign_model = campaign.model or "claude-sonnet-4-20250514"

    haiku = ClaudeClient(HAIKU)
    content_client = ClaudeClient(campaign_model)

    total_input = 0
    total_output = 0
    total_cost = Decimal("0")

    # ---- Step 3: outline (standard, not overridden by template) ----
    niche = site_ctx.niche if site_ctx else "general"
    audience = site_ctx.target_audience if site_ctx else "general audience"
    tone = site_ctx.tone if site_ctx else "professional"

    sys_p, usr_p = outline_generator(
        keyword=test_keyword,
        search_intent="informational",
        niche=niche,
        target_audience=audience,
        tone=tone,
        language=language,
    )
    outline_result = await haiku.call(sys_p, usr_p, max_tokens=1024)
    total_input += outline_result.input_tokens
    total_output += outline_result.output_tokens
    total_cost += outline_result.cost_usd

    outline_data = _parse_json_safe(outline_result.text)

    # ---- Build variable map for template substitution ----
    site_ctx_str = (
        f"Niche: {niche}\n"
        f"Target audience: {audience}\n"
        f"Tone: {tone}"
    )
    author_str = ""
    if site_ctx and site_ctx.author_name:
        author_str = f"Author: {site_ctx.author_name}"
        if site_ctx.author_credentials:
            author_str += f" ({site_ctx.author_credentials})"

    # Gather some existing slugs for internal links
    slug_rows = await db.execute(
        select(GeneratedPage.slug)
        .join(Keyword, Keyword.id == GeneratedPage.keyword_id)
        .join(Campaign, Campaign.id == Keyword.campaign_id)
        .where(Campaign.project_id == campaign.project_id)
        .where(GeneratedPage.slug.is_not(None))
        .limit(20)
    )
    slugs = [r[0] for r in slug_rows.all()]
    links_str = "\n".join(f"/{s}" for s in slugs) if slugs else "(none yet)"

    var_map = {
        "keyword": test_keyword,
        "site_context": site_ctx_str,
        "outline": json.dumps(outline_data, ensure_ascii=False, indent=2),
        "author_context": author_str or "(no author configured)",
        "internal_links_context": links_str,
    }

    # ---- Step 4: content using template prompts ----
    rendered_system = _substitute(template.system_prompt, var_map)
    rendered_user = _substitute(template.user_prompt, var_map)

    content_result = await content_client.call(
        rendered_system, rendered_user, max_tokens=4096
    )
    total_input += content_result.input_tokens
    total_output += content_result.output_tokens
    total_cost += content_result.cost_usd

    # Extract a readable preview
    parsed = _parse_json_safe(content_result.text)
    preview = (
        parsed.get("content_html")
        or parsed.get("content")
        or content_result.text
    )
    # Strip HTML tags for preview
    plain = re.sub(r"<[^>]+>", " ", preview)
    plain = re.sub(r"\s+", " ", plain).strip()[:_MAX_PREVIEW]

    elapsed = time.perf_counter() - t0

    return {
        "content_preview": plain,
        "tokens_used": total_input + total_output,
        "cost_usd": float(total_cost),
        "time_seconds": round(elapsed, 2),
    }
