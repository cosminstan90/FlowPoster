from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


KEYWORD_STATUS = Literal[
    "pending", "queued", "generating", "draft", "approved", "published", "error"
]


class KeywordCreate(BaseModel):
    campaign_id: UUID
    keyword: str = Field(..., max_length=500)
    search_intent: str | None = Field(None, max_length=50)
    page_type: str | None = Field(None, max_length=50)
    search_volume: int | None = None
    keyword_difficulty: int | None = None
    cpc_usd: Decimal | None = None
    source: str = "manual"


class KeywordStatusUpdate(BaseModel):
    status: KEYWORD_STATUS


class ImportPasteRequest(BaseModel):
    campaign_id: UUID
    text: str


class ImportResult(BaseModel):
    imported: int
    skipped: int
    duplicates: int
    cross_campaign_warnings: list[str] = []


class KeywordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    campaign_id: UUID
    keyword: str
    search_intent: str | None
    page_type: str | None
    status: str
    search_volume: int | None = None
    keyword_difficulty: int | None = None
    cpc_usd: Decimal | None = None
    source: str = "manual"
    error_message: str | None
    cluster_id: UUID | None = None
    cluster_role: str | None = None
    created_at: datetime
    updated_at: datetime


# ── Clustering ────────────────────────────────────────────────────────────────

class ClusterRequest(BaseModel):
    campaign_id: UUID
    keyword_ids: list[UUID] = []   # empty = all pending keywords in campaign


class ClusterKeywordSummary(BaseModel):
    keyword: str
    keyword_id: UUID
    role: str   # primary | secondary | standalone


class ClusterResult(BaseModel):
    cluster_id: str
    cluster_name: str
    primary_keyword: str
    secondary_keywords: list[str]
    recommendation: str
    reasoning: str
    keywords: list[ClusterKeywordSummary]


class ClusterResponse(BaseModel):
    clusters: list[ClusterResult]
    total_clustered: int


class PaginatedKeywords(BaseModel):
    items: list[KeywordOut]
    total: int
    page: int
    limit: int
    pages: int
