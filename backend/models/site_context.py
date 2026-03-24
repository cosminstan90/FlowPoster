import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class SiteContext(Base):
    __tablename__ = "site_contexts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), unique=True, nullable=False
    )
    niche: Mapped[str] = mapped_column(String(255), nullable=False)
    target_audience: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str] = mapped_column(String(50), nullable=False)
    topics_to_avoid: Mapped[str | None] = mapped_column(Text, nullable=True)
    competitor_urls: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    sitemap_urls: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_credentials: Mapped[str | None] = mapped_column(String(255), nullable=True)
    site_founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    editorial_policy_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="site_context")
