"""
Section regeneration service — rewrites individual parts of a GeneratedPage.
"""
from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.generated_page import GeneratedPage
from backend.services.ai.claude_client import ClaudeClient
from backend.services.ai.prompts import (
    body_regenerator,
    faq_regenerator,
    intro_regenerator,
    meta_regenerator,
)

SUPPORTED_SECTIONS = {"intro", "body", "faq", "meta"}


async def regenerate_section(
    page: GeneratedPage,
    section: str,
    language: str,
    niche: str,
    tone: str,
    keyword_text: str,
    db: AsyncSession,
) -> dict:
    """Regenerate one section and persist changes. Returns updated fields."""
    if section not in SUPPORTED_SECTIONS:
        raise ValueError(f"Unknown section '{section}'. Choose from {SUPPORTED_SECTIONS}.")

    client = ClaudeClient()

    if section == "intro":
        sys_p, usr_p = intro_regenerator(
            keyword=keyword_text,
            current_html=page.content_html or "",
            niche=niche,
            tone=tone,
            language=language,
        )
        result = await client.call(system=sys_p, user=usr_p, model="haiku", max_tokens=800)
        # Replace intro paragraphs at start of content (first <p> block)
        new_intro = result.content.strip()
        rest = _strip_intro(page.content_html or "")
        page.content_html = new_intro + "\n" + rest
        return {"content_html": page.content_html}

    elif section == "body":
        sys_p, usr_p = body_regenerator(
            keyword=keyword_text,
            current_html=page.content_html or "",
            niche=niche,
            tone=tone,
            language=language,
        )
        result = await client.call(system=sys_p, user=usr_p, model="sonnet", max_tokens=2000)
        page.content_html = result.content.strip()
        return {"content_html": page.content_html}

    elif section == "faq":
        sys_p, usr_p = faq_regenerator(
            keyword=keyword_text,
            faq_items=page.faq_items or [],
            language=language,
        )
        result = await client.call(system=sys_p, user=usr_p, model="haiku", max_tokens=1200)
        try:
            new_faq = json.loads(result.content.strip())
            if isinstance(new_faq, list):
                page.faq_items = new_faq
        except json.JSONDecodeError:
            pass
        return {"faq_items": page.faq_items}

    elif section == "meta":
        sys_p, usr_p = meta_regenerator(
            keyword=keyword_text,
            title=page.title or "",
            content_snippet=page.content_html or "",
            language=language,
        )
        result = await client.call(system=sys_p, user=usr_p, model="haiku", max_tokens=300)
        try:
            meta = json.loads(result.content.strip())
            if meta.get("title"):
                page.title = meta["title"]
            if meta.get("meta_description"):
                page.meta_description = meta["meta_description"]
            if meta.get("slug"):
                page.slug = meta["slug"]
        except json.JSONDecodeError:
            pass
        return {
            "title": page.title,
            "meta_description": page.meta_description,
            "slug": page.slug,
        }

    return {}


def _strip_intro(html: str) -> str:
    """Remove leading <p> tags (intro) from HTML body."""
    import re
    # Drop contiguous leading <p>...</p> blocks
    pattern = re.compile(r"^(\s*<p>.*?</p>\s*){1,3}", re.DOTALL | re.IGNORECASE)
    return pattern.sub("", html).strip()
