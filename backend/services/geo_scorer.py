"""
GEO Scorer — pure Python, no API call.
Calculates a 0-100 geo_score with per-factor breakdown.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GeoScore:
    score: int
    breakdown: dict[str, Any]
    citation_density: float


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _word_count(text: str) -> int:
    return len(text.split())


def _sentence_avg_length(text: str) -> float:
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0.0
    return sum(len(s.split()) for s in sentences) / len(sentences)


def score_geo(
    content_html: str,
    keyword: str,
    direct_answer: str,
    speakable_sections: list[str],
    has_comparison_table: bool,
    schema_markup: dict | None,
    faq_items: list[dict],
    author_name: str | None = None,
) -> GeoScore:
    """
    Score GEO quality 0-100 with 8 factors:
    1. direct_answer_present     — 20 pts
    2. speakable_sections >= 3   — 15 pts
    3. qa_structure              — 15 pts
    4. statistics_count >= 2     — 10 pts
    5. author_schema_present     — 10 pts
    6. definition_in_intro       — 10 pts
    7. comparison_table          — 10 pts
    8. avg_sentence_length < 20  — 10 pts
    """
    plain = _strip_tags(content_html)
    total_words = _word_count(plain)
    breakdown: dict[str, Any] = {}
    score = 0

    # 1. Direct answer: first paragraph ≤60 words, contains keyword
    da_ok = False
    if direct_answer:
        da_words = _word_count(direct_answer)
        kw_lower = keyword.lower()
        da_lower = direct_answer.lower()
        da_ok = da_words <= 60 and kw_lower in da_lower
    # Also check first paragraph of HTML
    if not da_ok:
        first_p = re.search(r"<p[^>]*>(.*?)</p>", content_html, re.DOTALL | re.IGNORECASE)
        if first_p:
            fp_text = _strip_tags(first_p.group(1))
            fp_words = _word_count(fp_text)
            da_ok = fp_words <= 60 and keyword.lower() in fp_text.lower()
    pts = 20 if da_ok else 0
    score += pts
    breakdown["direct_answer"] = {"points": pts, "max": 20, "ok": da_ok}

    # 2. Speakable sections >= 3
    speakable_ok = len(speakable_sections) >= 3
    # Also check HTML comments
    comment_count = len(re.findall(r"<!--\s*speakable\s*-->", content_html, re.IGNORECASE))
    speakable_ok = speakable_ok or comment_count >= 3
    pts = 15 if speakable_ok else (8 if (len(speakable_sections) >= 1 or comment_count >= 1) else 0)
    score += pts
    breakdown["speakable_sections"] = {"points": pts, "max": 15, "ok": speakable_ok, "count": max(len(speakable_sections), comment_count)}

    # 3. Q&A structure: H3 questions + short paragraphs, or FAQ items >= 3
    h3_questions = re.findall(r"<h3[^>]*>[^<]*\?[^<]*</h3>", content_html, re.IGNORECASE)
    qa_ok = len(h3_questions) >= 3 or len(faq_items) >= 3
    pts = 15 if qa_ok else (8 if (len(h3_questions) >= 1 or len(faq_items) >= 1) else 0)
    score += pts
    breakdown["qa_structure"] = {"points": pts, "max": 15, "ok": qa_ok, "h3_questions": len(h3_questions)}

    # 4. Statistics: numbers with % or "according to" citations
    stat_patterns = [
        r"\d+[\.,]?\d*\s*%",
        r"(?:according to|conform|potrivit|sursa|studiu)[^.]{5,50}",
        r"\d{4}[\s,]\d+(?:\.\d+)?(?:\s*(?:milioane?|mii|billion|million))?",
    ]
    stats_count = 0
    for pat in stat_patterns:
        stats_count += len(re.findall(pat, plain, re.IGNORECASE))
    stats_ok = stats_count >= 2
    pts = 10 if stats_ok else (5 if stats_count >= 1 else 0)
    score += pts
    breakdown["statistics"] = {"points": pts, "max": 10, "ok": stats_ok, "count": stats_count}

    # 5. Author schema
    author_ok = False
    if schema_markup:
        schema_str = str(schema_markup)
        author_ok = "author" in schema_str.lower() or (author_name and author_name in schema_str)
    if not author_ok and author_name:
        author_ok = author_name.lower() in plain.lower()
    pts = 10 if author_ok else 0
    score += pts
    breakdown["author_schema"] = {"points": pts, "max": 10, "ok": author_ok}

    # 6. Definition in intro: keyword defined in first 100 words
    first_100 = " ".join(plain.split()[:100])
    def_patterns = [
        rf"{re.escape(keyword)}\s+(?:este|reprezintă|înseamnă|is\s+a|refers to|means)[^.]+\.",
        r"(?:reprezintă|este\s+(?:un|o|cel)|is defined as|can be defined)[^.]+\.",
    ]
    def_ok = any(re.search(p, first_100, re.IGNORECASE) for p in def_patterns)
    pts = 10 if def_ok else 0
    score += pts
    breakdown["definition_intro"] = {"points": pts, "max": 10, "ok": def_ok}

    # 7. Comparison table
    table_ok = has_comparison_table or bool(re.search(r"<table", content_html, re.IGNORECASE))
    pts = 10 if table_ok else 0
    score += pts
    breakdown["comparison_table"] = {"points": pts, "max": 10, "ok": table_ok}

    # 8. Avg sentence length < 20 words
    avg_sent = _sentence_avg_length(plain)
    short_ok = 0 < avg_sent < 20
    pts = 10 if short_ok else 0
    score += pts
    breakdown["sentence_length"] = {"points": pts, "max": 10, "ok": short_ok, "avg_words": round(avg_sent, 1)}

    # Citation density: statistics per 100 words
    cite_density = round((stats_count / max(total_words, 1)) * 100, 2)

    return GeoScore(
        score=min(100, score),
        breakdown=breakdown,
        citation_density=cite_density,
    )
