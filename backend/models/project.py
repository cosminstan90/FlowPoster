import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    monthly_budget_usd: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, server_default="0"
    )
    cms_type: Mapped[str] = mapped_column(
        Enum("wordpress", "php_custom", "velocitycms", "dreamcms", name="cms_type_enum"),
        nullable=False,
    )
    cms_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    budget_alert_level: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="none"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    site_context: Mapped["SiteContext"] = relationship(
        "SiteContext", back_populates="project", uselist=False
    )
    campaigns: Mapped[list["Campaign"]] = relationship(
        "Campaign", back_populates="project"
    )
