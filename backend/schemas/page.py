from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FaqItem(BaseModel):
    question: str
    answer: str


class InternalLink(BaseModel):
    text: str
    slug: str


class BreadcrumbContext(BaseModel):
    project_id: uuid.UUID
    project_name: str
    campaign_id: uuid.UUID
    campaign_name: str
    keyword_text: str


class PageDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    keyword_id: uuid.UUID
    title: str | None
    slug: str | None
    meta_description: str | None
    summary_html: str | None = None
    content_html: str | None
    schema_markup: dict | None
    faq_items: list
    internal_links_suggested: list
    word_count: int
    quality_score: int
    readability_score: float | None
    intent_validation_passed: bool | None
    intent_validation_issues: list
    featured_image_url: str | None
    featured_image_credit: str | None
    input_tokens: int
    output_tokens: int
    model_used: str | None
    cost_usd: float
    status: str
    published_url: str | None
    published_at: datetime | None
    approved_at: datetime | None
    created_at: datetime
    breadcrumb: BreadcrumbContext | None = None
    geo_score: int | None = None
    geo_breakdown: dict | None = None
    speakable_sections: list | None = None
    geo_version: str | None = None
    has_direct_answer: bool = False
    has_comparison_table: bool = False
    citation_density: float | None = None


class PageUpdateRequest(BaseModel):
    title: str | None = None
    slug: str | None = None
    meta_description: str | None = None
    content_html: str | None = None
    schema_markup: dict | None = None
    faq_items: list | None = None
    internal_links_suggested: list | None = None
    featured_image_url: str | None = None
    featured_image_credit: str | None = None


class PageStatusUpdate(BaseModel):
    status: str


class RegenerateRequest(BaseModel):
    section: str  # intro | body | faq | meta


class FindImageResult(BaseModel):
    url: str | None
    credit: str | None
