from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


VALID_SCOPES = {"import_keywords", "read_campaigns", "publish_pages"}


class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=list)
    project_id: uuid.UUID | None = None

    def validated_scopes(self) -> list[str]:
        invalid = set(self.scopes) - VALID_SCOPES
        if invalid:
            raise ValueError(f"Invalid scopes: {invalid}. Valid: {VALID_SCOPES}")
        return self.scopes


class APIKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    key_masked: str  # "sk-XXXX...last4"
    scopes: list[str]
    project_id: uuid.UUID | None
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyOut):
    """Returned only on creation — includes the full key (shown once)."""
    full_key: str
