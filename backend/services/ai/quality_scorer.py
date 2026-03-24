"""
Step 8 — Quality Scorer (pure Python, no API call).

Calculates a 0-100 score from:
  word_count >= 600        → 20 pts
  keyword in title         → 15 pts
  h2 count >= 3            → 15 pts
  FAQ present              → 10 pts
  schema valid JSON        → 10 pts
  meta_description 120-155 → 10 pts
  Flesch readability       → 20 pts
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal


def _count_syllables(word: str) -> int:
    """Rough English syllable count (works okay for Romance languages too)."""
    word = word.lower()
    if len(word) <= 3:
        return 1
    word = re.sub(r"(?:es|ed|e)$", "", word) or word
    vowels = re.findall(r"[aeiouyăâîțșéèêëàùûü]+", word)
    return max(1, len(vowels))


def _flesch_score(text: str) -> float:
    """Flesch Reading Ease (0-100+). Higher = easier to read."""
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r"\w+", text)
    if not sentences or not words:
        return 0.0
    total_syllables = sum(_count_syllables(w) for w in words)
    avg_sentence_len = len(words) / len(sentences)
    avg_syllables = total_syllables / len(words)
    return 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables)


@dataclass
class QualityResult:
    score: int
    readability_score: Decimal
    word_count: int


def score(
    content_html: str | None,
    title: str | None,
    keyword: str,
    faq_items: list,
    schema_markup: dict | str | None,
    meta_description: str | None,
) -> QualityResult:
    points = 0

    # --- strip HTML for text analysis ---
    plain = re.sub(r"<[^>]+>", " ", content_html or "")
    plain = re.sub(r"\s+", " ", plain).strip()
    words = plain.split()
    word_count = len(words)

    # 1. word_count >= 600 → 20 pts
    if word_count >= 600:
        points += 20
    elif word_count >= 300:
        points += int(20 * (word_count / 600))

    # 2. keyword in title → 15 pts
    if title and keyword.lower() in title.lower():
        points += 15

    # 3. h2 count >= 3 → 15 pts
    h2_count = len(re.findall(r"<h2[\s>]", content_html or "", re.IGNORECASE))
    if h2_count >= 3:
        points += 15
    elif h2_count >= 1:
        points += int(15 * (h2_count / 3))

    # 4. FAQ present → 10 pts
    if faq_items and len(faq_items) > 0:
        points += 10

    # 5. schema valid JSON → 10 pts
    schema_valid = False
    if schema_markup:
        try:
            obj = json.loads(schema_markup) if isinstance(schema_markup, str) else schema_markup
            if isinstance(obj, dict):
                schema_valid = True
        except (json.JSONDecodeError, TypeError):
            pass
    if schema_valid:
        points += 10

    # 6. meta_description 120-155 chars → 10 pts
    if meta_description:
        md_len = len(meta_description)
        if 120 <= md_len <= 155:
            points += 10
        elif 80 <= md_len <= 200:
            points += 5

    # 7. Flesch readability → 20 pts
    flesch = _flesch_score(plain)
    # 60-70 is ideal; give proportional credit for 30-100 range
    flesch_clamped = max(0.0, min(100.0, flesch))
    if flesch_clamped >= 60:
        points += 20
    elif flesch_clamped >= 30:
        points += int(20 * ((flesch_clamped - 30) / 30))

    return QualityResult(
        score=min(100, points),
        readability_score=Decimal(str(round(flesch_clamped, 2))),
        word_count=word_count,
    )
