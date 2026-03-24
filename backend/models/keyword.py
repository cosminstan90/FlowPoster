import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False
    )
    keyword: Mapped[str] = mapped_column(String(500), nullable=False)
    search_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    page_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "queued",
            "generating",
            "draft",
            "approved",
            "published",
            "error",
            name="keyword_status_enum",
        ),
        nullable=False,
        server_default="pending",
    )
    search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    keyword_difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpc_usd: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, server_default="manual")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, onupdate=func.now()
    )

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="keywords")
    generated_pages: Mapped[list["GeneratedPage"]] = relationship(
        "GeneratedPage", back_populates="keyword"
    )
