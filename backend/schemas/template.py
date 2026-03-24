from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TemplateCreate(BaseModel):
    name: str
    type: str
    system_prompt: str
    user_prompt: str
    variables: list[str] = []
    is_active: bool = True


class TemplateUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    system_prompt: str | None = None
    user_prompt: str | None = None
    variables: list[str] | None = None
    is_active: bool | None = None


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str
    system_prompt: str
    user_prompt: str
    variables: list
    is_active: bool
    created_at: datetime
    campaigns_count: int = 0


class TemplateTestRequest(BaseModel):
    test_keyword: str
    campaign_id: uuid.UUID


class TemplateTestResult(BaseModel):
    content_preview: str
    tokens_used: int
    cost_usd: float
    time_seconds: float
