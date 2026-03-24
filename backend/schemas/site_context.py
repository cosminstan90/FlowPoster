from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SiteContextUpsert(BaseModel):
    niche: str
    target_audience: str
    tone: str
    topics_to_avoid: str | None = None
    competitor_urls: list[str] = []
    sitemap_urls: list[str] = []
    author_name: str | None = None
    author_bio: str | None = None
    author_credentials: str | None = None
    site_founded_year: int | None = None
    editorial_policy_url: str | None = None


class SiteContextOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    niche: str
    target_audience: str
    tone: str
    topics_to_avoid: str | None
    competitor_urls: list
    sitemap_urls: list
    author_name: str | None
    author_bio: str | None
    author_credentials: str | None
    site_founded_year: int | None
    editorial_policy_url: str | None
    updated_at: datetime
