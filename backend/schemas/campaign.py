from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PublishSchedule(BaseModel):
    pages_per_day: int
    time_of_day: str


class CampaignCreate(BaseModel):
    project_id: UUID
    name: str
    description: str | None = None
    model: str = "claude-sonnet-4-20250514"
    language: str = "ro"
    status: Literal["active", "paused", "completed"] = "active"
    publish_schedule: PublishSchedule | None = None
    prompt_template_id: UUID | None = None
    geo_enabled: bool = False
    geo_mode: str = "balanced"


class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    model: str | None = None
    language: str | None = None
    status: Literal["active", "paused", "completed"] | None = None
    publish_schedule: PublishSchedule | None = None
    prompt_template_id: UUID | None = None
    geo_enabled: bool | None = None
    geo_mode: str | None = None


class KeywordCounts(BaseModel):
    total: int
    pending: int
    queued: int
    generating: int
    draft: int
    approved: int
    published: int
    error: int


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    description: str | None
    model: str
    language: str
    status: str
    publish_schedule: dict[str, Any] | None
    prompt_template_id: UUID | None
    created_at: datetime
    geo_enabled: bool = False
    geo_mode: str = "balanced"


class CampaignDetail(CampaignOut):
    keyword_counts: KeywordCounts
