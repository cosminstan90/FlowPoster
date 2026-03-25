"""
Keyword clustering via Claude Haiku.

Groups semantically related keywords into clusters so that related terms can be
targeted together on a single pillar page or kept as separate pages.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.keyword import Keyword
from backend.services.ai.claude_client import ClaudeClient

logger = logging.getLogger(__name__)

_HAIKU = "claude-haiku-4-5-20251001"

_SYSTEM = (
    "You are an expert SEO strategist. Your task is to cluster a list of keywords "
    "into semantically related groups to guide content strategy."
)

_PROMPT_TPL = """\
Given the following keyword list, group them into semantically related clusters.

Keywords:
{keywords}

Return ONLY a valid JSON array. Each element must have exactly these fields:
- "cluster_name": short descriptive name for the group (string)
- "primary_keyword": the single best keyword to target for this cluster (string, must be from the list)
- "secondary_keywords": list of other keywords that can be covered on the same page (list of strings, each must be from the list)
- "recommendation": one of "one_page_pillar", "separate_pages", or "merge_with_primary"
- "reasoning": one sentence explaining the grouping strategy (string)

Rules:
- Every keyword must appear in exactly one cluster (either as primary or secondary).
- A cluster with recommendation "separate_pages" may have an empty secondary_keywords list.
- Do not invent keywords not present in the original list.
- Return only the JSON array, no markdown fences.
"""


@dataclass
class Cluster:
    cluster_id: uuid.UUID
    cluster_name: str
    primary_keyword: str
    secondary_keywords: list[str]
    recommendation: str  # one_page_pillar | separate_pages | merge_with_primary
    reasoning: str
    keyword_ids: dict[str, uuid.UUID] = field(default_factory=dict)  # keyword_text → db id


async def cluster_keywords(
    keyword_ids: list[uuid.UUID],
    campaign_id: uuid.UUID,
    db: AsyncSession,
) -> list[Cluster]:
    """
    Fetch keywords, call Claude Haiku to cluster them, persist assignments, return clusters.
    """
    # ── 1. Fetch keyword rows ──────────────────────────────────────────────────
    stmt = select(Keyword).where(
        Keyword.id.in_(keyword_ids),
        Keyword.campaign_id == campaign_id,
    )
    result = await db.execute(stmt)
    rows: list[Keyword] = list(result.scalars().all())

    if not rows:
        return []

    kw_map: dict[str, uuid.UUID] = {r.keyword: r.id for r in rows}  # text → db id
    kw_list = list(kw_map.keys())

    # ── 2. Call Claude Haiku ───────────────────────────────────────────────────
    client = ClaudeClient(_HAIKU)
    prompt = _PROMPT_TPL.format(keywords="\n".join(f"- {k}" for k in kw_list))

    try:
        call_result = await client.call(system=_SYSTEM, user=prompt, max_tokens=4096)
        raw_json = call_result.text.strip()
        # Strip accidental markdown fences
        if raw_json.startswith("```"):
            raw_json = "\n".join(
                line for line in raw_json.splitlines()
                if not line.startswith("```")
            )
        data = json.loads(raw_json)
    except Exception as exc:
        logger.error("Keyword clustering failed: %s", exc)
        raise

    # ── 3. Build Cluster objects ───────────────────────────────────────────────
    clusters: list[Cluster] = []
    for item in data:
        cid = uuid.uuid4()
        primary = item.get("primary_keyword", "")
        secondaries: list[str] = item.get("secondary_keywords", [])

        c = Cluster(
            cluster_id=cid,
            cluster_name=item.get("cluster_name", "Cluster"),
            primary_keyword=primary,
            secondary_keywords=secondaries,
            recommendation=item.get("recommendation", "separate_pages"),
            reasoning=item.get("reasoning", ""),
            keyword_ids={
                kw: kw_map[kw]
                for kw in ([primary] + secondaries)
                if kw in kw_map
            },
        )
        clusters.append(c)

    # ── 4. Persist cluster assignments ────────────────────────────────────────
    assigned: set[uuid.UUID] = set()
    for cluster in clusters:
        # Primary keyword
        if cluster.primary_keyword in kw_map:
            db_id = kw_map[cluster.primary_keyword]
            kw_row = next((r for r in rows if r.id == db_id), None)
            if kw_row:
                kw_row.cluster_id = cluster.cluster_id
                kw_row.cluster_role = "primary"
                assigned.add(db_id)

        # Secondary keywords
        for sec in cluster.secondary_keywords:
            if sec in kw_map:
                db_id = kw_map[sec]
                kw_row = next((r for r in rows if r.id == db_id), None)
                if kw_row:
                    kw_row.cluster_id = cluster.cluster_id
                    kw_row.cluster_role = "secondary"
                    assigned.add(db_id)

    # Any keyword not assigned to a cluster → standalone
    for row in rows:
        if row.id not in assigned:
            row.cluster_id = uuid.uuid4()
            row.cluster_role = "standalone"

    await db.flush()

    return clusters
