import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default="claude-sonnet-4-20250514"
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="ro")
    status: Mapped[str] = mapped_column(
        Enum("active", "paused", "completed", name="campaign_status_enum"),
        nullable=False,
        server_default="active",
    )
    publish_schedule: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prompt_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompt_templates.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="campaigns")
    prompt_template: Mapped["PromptTemplate | None"] = relationship(
        "PromptTemplate", back_populates="campaigns"
    )
    keywords: Mapped[list["Keyword"]] = relationship(
        "Keyword", back_populates="campaign"
    )
