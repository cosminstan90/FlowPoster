"""
GEO Schema generator — pure Python, no API call.
Generates SpeakableSpecification, QAPage, HowTo, DefinedTerm schemas.
Merges them into one JSON-LD block alongside the existing Article/FAQ schema.
"""
from __future__ import annotations
import json, re
from typing import Any


def _speakable_spec(speakable_sections: list[str]) -> dict:
    """Generate SpeakableSpecification for marked sections."""
    if not speakable_sections:
        return {}
    css_selectors = [".speakable"] + [f'h2:-soup-contains("{s}")' for s in speakable_sections[:5]]
    return {
        "@type": "SpeakableSpecification",
        "cssSelector": css_selectors,
    }


def _qa_page_schema(title: str, faq_items: list[dict]) -> dict | None:
    if not faq_items:
        return None
    main_entity = []
    for item in faq_items[:10]:
        q = item.get("question", "")
        a = item.get("answer", "")
        if q and a:
            main_entity.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            })
    if not main_entity:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "QAPage",
        "name": title,
        "mainEntity": main_entity,
    }


def _howto_schema(keyword: str, content_html: str, title: str) -> dict | None:
    """Extract steps from ordered list or numbered headings."""
    steps = []
    # Look for <li> items as steps
    items = re.findall(r"<li[^>]*>(.*?)</li>", content_html, re.DOTALL | re.IGNORECASE)
    for item in items[:8]:
        text = re.sub(r"<[^>]+>", "", item).strip()
        if text and len(text) > 10:
            steps.append({"@type": "HowToStep", "text": text})
    if len(steps) < 2:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": title,
        "description": f"How to {keyword}",
        "step": steps,
    }


def _defined_term_schema(keyword: str, definition: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "name": keyword,
        "description": definition,
        "inDefinedTermSet": {
            "@type": "DefinedTermSet",
            "name": "SEO Publisher Knowledge Base",
        },
    }


def _extract_definition(content_html: str, keyword: str) -> str | None:
    """Try to extract a definition from the first 200 words."""
    plain = re.sub(r"<[^>]+>", " ", content_html)
    words = plain.split()[:200]
    text = " ".join(words)
    # Look for "X este/is ..." patterns
    patterns = [
        rf"{re.escape(keyword)}\s+(?:este|reprezintă|înseamnă|is|refers to|means)[^.]+\.",
        r"(?:definit[ăa]|defined as|este\s+un)[^.]+\.",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()[:300]
    return None


def build_geo_schema(
    existing_schema: dict | None,
    title: str,
    keyword: str,
    content_html: str,
    speakable_sections: list[str],
    faq_items: list[dict],
    is_howto: bool = False,
    is_concept: bool = False,
    has_qa: bool = False,
) -> dict:
    """
    Merge GEO-specific schema blocks with existing Article/FAQ schema.
    Returns an @graph JSON-LD object.
    """
    graph: list[dict] = []

    # Existing schema
    if existing_schema:
        if "@graph" in existing_schema:
            graph.extend(existing_schema["@graph"])
        elif "@type" in existing_schema:
            graph.append(existing_schema)

    # Speakable
    speakable = _speakable_spec(speakable_sections)
    if speakable:
        # Add speakable to Article if present, else as standalone
        for item in graph:
            if item.get("@type") in ("Article", "BlogPosting", "NewsArticle"):
                item["speakable"] = speakable
                break
        else:
            graph.append({
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": title,
                "speakable": speakable,
            })

    # QAPage
    if has_qa or faq_items:
        qa = _qa_page_schema(title, faq_items)
        if qa:
            graph.append(qa)

    # HowTo
    if is_howto:
        howto = _howto_schema(keyword, content_html, title)
        if howto:
            graph.append(howto)

    # DefinedTerm
    if is_concept:
        definition = _extract_definition(content_html, keyword)
        if definition:
            graph.append(_defined_term_schema(keyword, definition))

    return {
        "@context": "https://schema.org",
        "@graph": graph,
    }
