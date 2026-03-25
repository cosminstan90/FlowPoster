"""
GEO content generator — replaces Step 4 (content_gen) when campaign.geo_enabled=True.
Instructs Claude to produce AI-citability-optimized content.
"""
from __future__ import annotations
import json, re, logging
from dataclasses import dataclass
from backend.services.ai.claude_client import ClaudeClient, CallResult

logger = logging.getLogger(__name__)

GEO_VERSION = "1.0"

@dataclass
class GeoContentResult:
    content_html: str
    direct_answer: str
    speakable_sections: list[str]
    has_comparison_table: bool
    statistics_used: list[str]
    call_result: CallResult


async def generate_geo_content(
    keyword: str,
    search_intent: str,
    outline_json: str,
    niche: str,
    target_audience: str,
    tone: str,
    topics_to_avoid: str,
    author_name: str,
    author_bio: str,
    author_credentials: str,
    existing_slugs: list[str],
    language: str,
    geo_mode: str,
    model: str,
) -> GeoContentResult:
    client = ClaudeClient(model)

    mode_instructions = {
        "geo_first": "PRIORITY: Optimize for AI citability above all. Every paragraph must be a quotable, self-contained factual statement.",
        "seo_first": "PRIORITY: Traditional SEO structure with GEO enhancements. Follow outline closely, add direct answers as supplements.",
        "balanced": "BALANCE: Equal weight to SEO structure and AI citability. Each section should both rank well and be citation-worthy.",
    }
    mode_hint = mode_instructions.get(geo_mode, mode_instructions["balanced"])

    implies_comparison = any(w in keyword.lower() for w in ["vs", "versus", "compare", "comparatie", "diferenta", "cel mai bun", "best"])
    is_howto = keyword.lower().startswith(("cum ", "how ", "cum să", "how to", "cum se"))
    is_concept = search_intent in ("informational",) and not is_howto

    system_prompt = f"""You are an expert SEO and GEO (Generative Engine Optimization) content writer for {niche}.
Language: {language}
Tone: {tone}
Target audience: {target_audience}
{f'Avoid: {topics_to_avoid}' if topics_to_avoid else ''}
Author: {author_name} — {author_bio} — Credentials: {author_credentials}

{mode_hint}

GEO REQUIREMENTS (non-negotiable):
1. START with a Direct Answer Block: 2-3 sentences directly answering "{keyword}". No fluff. Under 60 words. Must contain the keyword.
2. {'Include a Definition Block: Define "' + keyword + '" in the first 150 words.' if is_concept else ''}
3. Use Q&A structure: H3 questions with short answers (under 50 words each) for at least 3 sub-topics.
4. Include at least 2 statistics or data points with inline source attribution (e.g., "According to [Source], X%...").
5. {'Add a comparison table with at least 3 rows.' if implies_comparison else 'Consider adding a comparison table if relevant.'}
6. Write citation-ready sentences: factual, specific, quotable. Each H2 section should start with a quotable claim.
7. Mark speakable sections: Add HTML comment <!-- speakable --> immediately BEFORE each paragraph that directly answers a question.
8. Internal links: use existing slugs where contextually relevant: {', '.join(existing_slugs[:10]) if existing_slugs else 'none yet'}.

Return ONLY valid JSON (no markdown fences):
{{
  "content_html": "<full HTML content with <!-- speakable --> markers>",
  "direct_answer": "<first 2-3 sentences, plain text>",
  "speakable_sections": ["<H2 title 1>", "<H2 title 2>"],
  "has_comparison_table": true/false,
  "statistics_used": ["<stat 1 with source>", "<stat 2 with source>"],
  "internal_links_used": [{{"text": "anchor text", "slug": "slug"}}]
}}"""

    user_prompt = f"""Write a comprehensive, GEO-optimized article for keyword: "{keyword}"
Search intent: {search_intent}
Outline to follow:
{outline_json}

Remember: Start with Direct Answer Block. Mark speakable paragraphs. Include statistics with sources."""

    result = await client.call(system_prompt, user_prompt, max_tokens=8192)

    # Parse
    text = result.text.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    data = json.loads(text)

    return GeoContentResult(
        content_html=data.get("content_html", ""),
        direct_answer=data.get("direct_answer", ""),
        speakable_sections=data.get("speakable_sections", []),
        has_comparison_table=bool(data.get("has_comparison_table", False)),
        statistics_used=data.get("statistics_used", []),
        call_result=result,
    )
