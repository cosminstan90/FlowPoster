import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class GeneratedPage(Base):
    __tablename__ = "generated_pages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keywords.id"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    slug: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_markup: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    faq_items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    internal_links_suggested: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )
    word_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    quality_score: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    readability_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    intent_validation_passed: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    intent_validation_issues: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )
    featured_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    featured_image_credit: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    input_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cost_usd: Mapped[float] = mapped_column(
        Numeric(10, 6), nullable=False, server_default="0"
    )
    status: Mapped[str] = mapped_column(
        Enum("draft", "approved", "published", "rejected", name="page_status_enum"),
        nullable=False,
        server_default="draft",
    )
    published_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    keyword: Mapped["Keyword"] = relationship(
        "Keyword", back_populates="generated_pages"
    )
