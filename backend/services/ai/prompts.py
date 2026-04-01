"""
System and user prompt templates for each pipeline step.

Every function returns (system_prompt, user_prompt) ready for ClaudeClient.call().
"""

from __future__ import annotations


# ------------------------------------------------------------------
# Step 1 – Intent Detector  (haiku)
# ------------------------------------------------------------------
def intent_detector(keyword: str, niche: str) -> tuple[str, str]:
    system = (
        "You are an SEO intent classifier. "
        "Respond with a single JSON object, no markdown fences."
    )
    user = (
        f"Classify the search intent of this keyword for a site in the '{niche}' niche.\n\n"
        f"Keyword: {keyword}\n\n"
        "Return JSON with exactly these fields:\n"
        '{"search_intent": "<informational|transactional|navigational|commercial>", '
        '"page_type": "<blog_post|product_page|landing_page|guide|comparison|listicle>", '
        '"difficulty": "<easy|medium|hard>"}'
    )
    return system, user


# ------------------------------------------------------------------
# Step 3 – Outline Generator  (campaign model)
# ------------------------------------------------------------------
def outline_generator(
    keyword: str,
    search_intent: str,
    niche: str,
    target_audience: str,
    tone: str,
    language: str,
) -> tuple[str, str]:
    system = (
        "You are an expert SEO content strategist. "
        f"Write all outlines in {language}. "
        "Respond with a single JSON object, no markdown fences."
    )
    user = (
        f"Create a content outline for the keyword '{keyword}'.\n\n"
        f"Search intent: {search_intent}\n"
        f"Niche: {niche}\n"
        f"Target audience: {target_audience}\n"
        f"Tone: {tone}\n\n"
        "Return JSON with exactly these fields:\n"
        '{"h2_sections": [{"title": "<string>", "description": "<brief guidance>"}], '
        '"faq_questions": ["<question 1>", "<question 2>", "<question 3>", "<question 4>", "<question 5>"]}'
    )
    return system, user


# ------------------------------------------------------------------
# Step 4 – Content Generator  (campaign model)
# ------------------------------------------------------------------
def content_generator(
    keyword: str,
    outline_json: str,
    niche: str,
    target_audience: str,
    tone: str,
    topics_to_avoid: str | None,
    author_name: str | None,
    author_bio: str | None,
    author_credentials: str | None,
    existing_slugs: list[str],
    language: str,
    secondary_keywords: list[str] | None = None,
) -> tuple[str, str]:
    system = (
        f"You are a senior SEO and GEO content writer. Write all content in {language}.\n"
        "Editorial rules (mandatory):\n"
        "- Never invent data, statistics, or facts. If uncertain, phrase it cautiously.\n"
        "- Write in short, digestible sentences and short paragraphs.\n"
        "- Avoid filler, repetition, and vague language.\n"
        "- Tone: friendly but expert. Style: clear, direct, factual (Axios-style).\n"
        "- Make content easy to scan and easy to extract by AI systems.\n"
        "SEO rules:\n"
        "- Include the main keyword naturally in the intro and relevant sections.\n"
        "- Cover the search intent completely. Use semantic variations.\n"
        "- No keyword stuffing.\n"
        "GEO rules:\n"
        "- Open with a direct answer (the summary).\n"
        "- Write clear, concise, self-contained sentences that are easy to cite.\n"
        "- Define important terms simply and precisely.\n"
        "Produce valid HTML using semantic tags (h2, h3, p, ul, ol, strong, em, table). "
        "Do NOT wrap the response in markdown fences. "
        "Respond with a single JSON object."
    )

    avoid = f"\nTopics to avoid: {topics_to_avoid}" if topics_to_avoid else ""
    author_ctx = ""
    if author_name:
        author_ctx = f"\nAuthor: {author_name}"
        if author_credentials:
            author_ctx += f" ({author_credentials})"
        if author_bio:
            author_ctx += f"\nAuthor bio: {author_bio}"

    sec_kw_str = ", ".join(secondary_keywords) if secondary_keywords else ""
    sec_kw_line = f"\nSecondary keywords: {sec_kw_str}" if sec_kw_str else ""
    slugs_str = ", ".join(existing_slugs[:50]) if existing_slugs else "(none yet)"

    user = (
        f"Write a complete article for the main keyword: '{keyword}'.\n"
        f"Niche: {niche}\n"
        f"Target audience: {target_audience}\n"
        f"Tone: {tone}\n"
        f"Goal: organic traffic{sec_kw_line}"
        f"{avoid}{author_ctx}\n\n"
        f"Approved outline:\n{outline_json}\n\n"
        f"Existing page slugs for internal linking:\n{slugs_str}\n\n"
        "Required article structure (in this order):\n"
        "1. summary_html — a 2-4 sentence direct answer, GEO-optimized, wrapped in <p> tag(s). "
        "This is the opening summary shown above the article.\n"
        "2. content_html — the full article body starting with a clear introduction, then:\n"
        "   - H2/H3 sections following the outline\n"
        "   - Tables where useful for comparison or synthesis\n"
        "   - FAQ section answering all questions from the outline\n"
        "   - Short conclusion\n\n"
        "Content requirements:\n"
        "- Minimum 1200 words in content_html.\n"
        "- Main keyword appears naturally in the introduction and relevant sections.\n"
        "- Use relative hrefs like /slug for internal links.\n\n"
        "Return JSON with exactly these keys:\n"
        '{"summary_html": "<2-4 sentence summary as HTML>", '
        '"content_html": "<full article HTML, without the summary>", '
        '"internal_links_used": [{"text": "<anchor text>", "slug": "<slug>"}]}'
    )
    return system, user


# ------------------------------------------------------------------
# Step 5 – SEO Layer  (haiku)
# ------------------------------------------------------------------
def seo_layer(content_html: str, keyword: str, language: str) -> tuple[str, str]:
    system = (
        "You are an SEO metadata specialist. "
        f"Write metadata in {language}. "
        "Respond with a single JSON object, no markdown fences."
    )
    # Send only first ~2000 chars to save tokens
    snippet = content_html[:2000]
    user = (
        f"Generate SEO metadata for an article targeting '{keyword}'.\n\n"
        f"Article start:\n{snippet}\n\n"
        "Return JSON:\n"
        '{"title": "<max 60 characters>", '
        '"meta_description": "<120-155 characters>", '
        '"slug": "<lowercase-hyphenated-slug>"}'
    )
    return system, user


# ------------------------------------------------------------------
# Step 6 – Schema Generator  (haiku)
# ------------------------------------------------------------------
def schema_generator(
    title: str,
    content_snippet: str,
    faq_questions: list[str],
    faq_html: str,
) -> tuple[str, str]:
    system = (
        "You are a structured-data specialist. "
        "Respond ONLY with a single valid JSON-LD script (no markdown fences, no extra text)."
    )
    faqs = "\n".join(f"- {q}" for q in faq_questions)
    user = (
        f"Create a combined Article + FAQPage JSON-LD schema for:\n\n"
        f"Title: {title}\n"
        f"FAQ questions:\n{faqs}\n\n"
        f"Content snippet:\n{content_snippet[:1000]}\n\n"
        "Return a single JSON-LD object using @graph to combine Article and FAQPage schemas."
    )
    return system, user


# ------------------------------------------------------------------
# Step 7 – Intent Validator  (haiku)
# ------------------------------------------------------------------
def intent_validator(
    keyword: str,
    search_intent: str,
    content_start: str,
) -> tuple[str, str]:
    system = (
        "You are a search intent QA reviewer. "
        "Respond with a single JSON object, no markdown fences."
    )
    user = (
        f"Does this content correctly address the search intent?\n\n"
        f"Keyword: {keyword}\n"
        f"Expected intent: {search_intent}\n\n"
        f"Content (first 300 words):\n{content_start}\n\n"
        "Return JSON:\n"
        '{"passes": <true|false>, "issues": ["<issue 1>", "..."]}'
    )
    return system, user


# ------------------------------------------------------------------
# Regeneration – Intro  (campaign model)
# ------------------------------------------------------------------
def intro_regenerator(
    keyword: str, current_html: str, niche: str, tone: str, language: str
) -> tuple[str, str]:
    system = (
        "You are a senior SEO copywriter. "
        f"Write in {language}. "
        "Return ONLY the new intro HTML, no JSON, no markdown fences."
    )
    snippet = current_html[:500]
    user = (
        f"Rewrite the introduction section for an article targeting '{keyword}'.\n\n"
        f"Niche: {niche}\nTone: {tone}\n\n"
        f"Current intro:\n{snippet}\n\n"
        "Write a compelling intro (2-3 paragraphs) using <p> tags. Return only the HTML."
    )
    return system, user


# ------------------------------------------------------------------
# Regeneration – Body  (campaign model)
# ------------------------------------------------------------------
def body_regenerator(
    keyword: str, current_html: str, niche: str, tone: str, language: str
) -> tuple[str, str]:
    system = (
        "You are a senior SEO copywriter. "
        f"Write in {language}. "
        "Produce valid HTML with semantic tags (h2, h3, p, ul, ol, strong, em). "
        "Return ONLY the new body HTML, no JSON, no markdown fences."
    )
    user = (
        f"Rewrite the main body content for an article targeting '{keyword}'.\n\n"
        f"Niche: {niche}\nTone: {tone}\n\n"
        f"Current content (for context):\n{current_html[:1500]}\n\n"
        "Write comprehensive body content (minimum 400 words) with h2 sections. Return only the HTML."
    )
    return system, user


# ------------------------------------------------------------------
# Regeneration – FAQ  (haiku)
# ------------------------------------------------------------------
def faq_regenerator(
    keyword: str, faq_items: list[dict], language: str
) -> tuple[str, str]:
    system = (
        "You are an SEO FAQ writer. "
        f"Write in {language}. "
        "Respond with a single JSON array, no markdown fences."
    )
    current = "\n".join(f"Q: {item.get('question', '')} A: {item.get('answer', '')[:100]}" for item in faq_items[:5])
    user = (
        f"Rewrite the FAQ section for an article targeting '{keyword}'.\n\n"
        f"Current FAQ:\n{current}\n\n"
        "Return a JSON array of 5 objects:\n"
        '[{"question": "<string>", "answer": "<2-3 sentence answer>"}]'
    )
    return system, user


# ------------------------------------------------------------------
# Regeneration – Meta  (haiku)
# ------------------------------------------------------------------
def meta_regenerator(
    keyword: str, title: str, content_snippet: str, language: str
) -> tuple[str, str]:
    system = (
        "You are an SEO metadata specialist. "
        f"Write in {language}. "
        "Respond with a single JSON object, no markdown fences."
    )
    user = (
        f"Rewrite the SEO metadata for an article targeting '{keyword}'.\n\n"
        f"Current title: {title}\n"
        f"Content snippet:\n{content_snippet[:500]}\n\n"
        "Return JSON:\n"
        '{"title": "<max 60 chars>", "meta_description": "<120-155 chars>", "slug": "<lowercase-hyphenated>"}'
    )
    return system, user
