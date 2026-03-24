from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GeneratedPageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    keyword_id: UUID
    title: str | None
    slug: str | None
    meta_description: str | None
    content_html: str | None
    schema_markup: dict[str, Any] | None
    faq_items: list
    internal_links_suggested: list
    word_count: int
    quality_score: int
    readability_score: Decimal | None
    intent_validation_passed: bool | None
    intent_validation_issues: list
    input_tokens: int
    output_tokens: int
    model_used: str | None
    cost_usd: Decimal
    status: str
    created_at: datetime


class BulkGenerateRequest(BaseModel):
    keyword_ids: list[UUID]
    campaign_id: UUID


class BulkEstimate(BaseModel):
    model: str
    keyword_count: int
    min_usd: Decimal
    max_usd: Decimal
    estimated_tokens: int


class BulkGenerateResult(BaseModel):
    queued: int
    keyword_ids: list[UUID]
    estimate: BulkEstimate
