from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.schemas.site_context import SiteContextOut


class ProjectCreate(BaseModel):
    name: str
    domain: str
    description: str | None = None
    monthly_budget_usd: Decimal = Decimal("0")
    cms_type: Literal["wordpress", "php_custom", "velocitycms", "dreamcms"]
    cms_config: dict[str, Any] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    description: str | None = None
    monthly_budget_usd: Decimal | None = None
    cms_type: Literal["wordpress", "php_custom", "velocitycms", "dreamcms"] | None = None
    cms_config: dict[str, Any] | None = None


class ProjectStats(BaseModel):
    total_keywords: int
    total_pages_published: int
    cost_this_month: Decimal


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    domain: str
    description: str | None
    monthly_budget_usd: Decimal
    cms_type: str
    cms_config: dict[str, Any] | None
    budget_alert_level: str = "none"
    created_at: datetime


class ProjectWithStats(ProjectOut):
    stats: ProjectStats


class ProjectDetail(ProjectWithStats):
    site_context: SiteContextOut | None
