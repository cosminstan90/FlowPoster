"""
Duplicate detection for keyword imports.

Same-campaign  : similarity > 85%  → skip (duplicate)
Cross-campaign : similarity > 90%  → warn but still import
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

# ---------------------------------------------------------------------------
# Stopwords (Romanian + English)
# ---------------------------------------------------------------------------
_STOPWORDS_EN: frozenset[str] = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "shall", "that", "this",
        "these", "those", "it", "its", "not", "no", "nor", "so", "yet",
        "both", "either", "neither", "each", "few", "more", "most", "other",
        "some", "such", "than", "then", "too", "very", "just", "about",
        "above", "after", "before", "between", "into", "through", "during",
        "without", "within", "along", "across", "behind", "beyond", "plus",
        "except", "up", "out", "around", "down", "off", "over", "under",
        "how", "what", "where", "when", "why", "who", "which",
    }
)

_STOPWORDS_RO: frozenset[str] = frozenset(
    {
        "un", "o", "si", "și", "sau", "dar", "in", "în", "pe", "la", "de",
        "cu", "din", "ca", "că", "sa", "să", "nu", "se", "mai", "fi", "fost",
        "este", "sunt", "era", "au", "ai", "al", "ale", "lui", "ei", "lor",
        "eu", "tu", "el", "ea", "noi", "voi", "ce", "care", "cine", "cand",
        "când", "unde", "cum", "cat", "cât", "daca", "dacă", "după", "dupa",
        "prin", "pentru", "despre", "intre", "între", "spre", "fata", "față",
        "pana", "până", "decat", "decât", "deci", "deja", "acum", "astfel",
        "atat", "atât", "acestea", "acest", "această", "acel", "aceea",
        "aceia", "acele", "cel", "cea", "cei", "cele", "tot", "toata",
        "toată", "toate", "toti", "toți", "orice", "oricare", "fiecare",
    }
)

STOPWORDS: frozenset[str] = _STOPWORDS_EN | _STOPWORDS_RO

# Keep letters (including diacritics), digits, and spaces
_CLEAN = re.compile(r"[^\w\s]", re.UNICODE)
_MULTI_SPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercase, remove punctuation, strip stopwords."""
    text = text.lower()
    text = _CLEAN.sub(" ", text)
    text = _MULTI_SPACE.sub(" ", text).strip()
    tokens = [t for t in text.split() if t not in STOPWORDS and t]
    return " ".join(tokens)


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    is_duplicate: bool
    """True → skip this keyword (too similar to one in the same campaign)."""
    cross_campaign_warning: str | None = None
    """Non-None → similar keyword exists in another campaign of the same project."""


class DuplicateGuard:
    """
    Stateful guard that accumulates accepted keywords so intra-batch
    duplicates are caught even before the first DB flush.

    Usage::

        guard = await DuplicateGuard.build(campaign_id, db)
        for kw in incoming:
            result = guard.check(kw)
            if result.is_duplicate:
                ...  # skip
            else:
                guard.accept(kw)   # register so next kw in batch sees it
                if result.cross_campaign_warning:
                    warnings.append(result.cross_campaign_warning)
    """

    SAME_CAMPAIGN_THRESHOLD: float = 0.85
    CROSS_CAMPAIGN_THRESHOLD: float = 0.90

    def __init__(
        self,
        campaign_norms: list[str],
        cross_norms: list[tuple[str, str]],  # (normalized_keyword, campaign_name)
    ) -> None:
        self._campaign: list[str] = campaign_norms
        self._cross: list[tuple[str, str]] = cross_norms

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    async def build(cls, campaign_id, db, exclude_keyword_id=None) -> "DuplicateGuard":
        """Load existing keywords from DB and construct the guard.

        Args:
            campaign_id: The campaign to load keywords from.
            db: Async DB session.
            exclude_keyword_id: Optional keyword ID to exclude from the
                same-campaign list (pass the ID of the keyword currently
                being processed so it doesn't match itself).
        """
        from sqlalchemy import select
        from backend.models import Campaign, Keyword

        # Existing keywords in this campaign (excluding the one being generated)
        stmt = select(Keyword.keyword).where(Keyword.campaign_id == campaign_id)
        if exclude_keyword_id is not None:
            stmt = stmt.where(Keyword.id != exclude_keyword_id)
        same_rows = await db.execute(stmt)
        campaign_norms = [normalize(r[0]) for r in same_rows.all()]

        # Keywords in other campaigns of the same project
        campaign_row = await db.execute(
            select(Campaign.project_id).where(Campaign.id == campaign_id)
        )
        project_id = campaign_row.scalar_one_or_none()

        cross_norms: list[tuple[str, str]] = []
        if project_id is not None:
            cross_rows = await db.execute(
                select(Keyword.keyword, Campaign.name)
                .join(Campaign, Campaign.id == Keyword.campaign_id)
                .where(Campaign.project_id == project_id)
                .where(Campaign.id != campaign_id)
            )
            cross_norms = [(normalize(kw), name) for kw, name in cross_rows.all()]

        return cls(campaign_norms, cross_norms)

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def check(self, keyword: str) -> CheckResult:
        norm = normalize(keyword)

        # --- same campaign check ---
        for existing in self._campaign:
            if _ratio(norm, existing) > self.SAME_CAMPAIGN_THRESHOLD:
                return CheckResult(is_duplicate=True)

        # --- cross-campaign check ---
        warning: str | None = None
        for existing_norm, campaign_name in self._cross:
            if _ratio(norm, existing_norm) > self.CROSS_CAMPAIGN_THRESHOLD:
                warning = (
                    f'"{keyword}" is similar to an existing keyword '
                    f'in campaign "{campaign_name}"'
                )
                break

        return CheckResult(is_duplicate=False, cross_campaign_warning=warning)

    def accept(self, keyword: str) -> None:
        """Register an accepted keyword so subsequent batch entries are checked against it."""
        self._campaign.append(normalize(keyword))
