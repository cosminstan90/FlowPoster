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
    created_at: datetime
    updated_at: datetime


class PaginatedKeywords(BaseModel):
    items: list[KeywordOut]
    total: int
    page: int
    limit: int
    pages: int
