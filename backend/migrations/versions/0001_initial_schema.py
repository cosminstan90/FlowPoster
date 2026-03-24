"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Enums ---
    cms_type_enum = postgresql.ENUM(
        "wordpress", "php_custom", name="cms_type_enum", create_type=False
    )
    campaign_status_enum = postgresql.ENUM(
        "active", "paused", "completed", name="campaign_status_enum", create_type=False
    )
    keyword_status_enum = postgresql.ENUM(
        "pending", "queued", "generating", "draft", "approved", "published", "error",
        name="keyword_status_enum", create_type=False,
    )
    page_status_enum = postgresql.ENUM(
        "draft", "approved", "published", "rejected",
        name="page_status_enum", create_type=False,
    )

    op.execute("CREATE TYPE cms_type_enum AS ENUM ('wordpress', 'php_custom')")
    op.execute("CREATE TYPE campaign_status_enum AS ENUM ('active', 'paused', 'completed')")
    op.execute(
        "CREATE TYPE keyword_status_enum AS ENUM "
        "('pending', 'queued', 'generating', 'draft', 'approved', 'published', 'error')"
    )
    op.execute("CREATE TYPE page_status_enum AS ENUM ('draft', 'approved', 'published', 'rejected')")

    # --- projects ---
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "monthly_budget_usd",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("cms_type", cms_type_enum, nullable=False),
        sa.Column("cms_config", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # --- site_contexts ---
    op.create_table(
        "site_contexts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("niche", sa.String(255), nullable=False),
        sa.Column("target_audience", sa.Text, nullable=False),
        sa.Column("tone", sa.String(50), nullable=False),
        sa.Column("topics_to_avoid", sa.Text, nullable=True),
        sa.Column(
            "competitor_urls",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "sitemap_urls",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("author_name", sa.String(255), nullable=True),
        sa.Column("author_bio", sa.Text, nullable=True),
        sa.Column("author_credentials", sa.String(255), nullable=True),
        sa.Column("site_founded_year", sa.Integer, nullable=True),
        sa.Column("editorial_policy_url", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- prompt_templates ---
    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("system_prompt", sa.Text, nullable=False),
        sa.Column("user_prompt", sa.Text, nullable=False),
        sa.Column(
            "variables",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # --- campaigns ---
    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "model",
            sa.String(100),
            nullable=False,
            server_default="claude-sonnet-4-20250514",
        ),
        sa.Column(
            "language", sa.String(10), nullable=False, server_default="ro"
        ),
        sa.Column(
            "status",
            campaign_status_enum,
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "publish_schedule",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "prompt_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompt_templates.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # --- keywords ---
    op.create_table(
        "keywords",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id"),
            nullable=False,
        ),
        sa.Column("keyword", sa.String(500), nullable=False),
        sa.Column("search_intent", sa.String(50), nullable=True),
        sa.Column("page_type", sa.String(50), nullable=True),
        sa.Column(
            "status",
            keyword_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- generated_pages ---
    op.create_table(
        "generated_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "keyword_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("keywords.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("slug", sa.String(500), nullable=True),
        sa.Column("meta_description", sa.String(500), nullable=True),
        sa.Column("content_html", sa.Text, nullable=True),
        sa.Column(
            "schema_markup",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "faq_items",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "internal_links_suggested",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("word_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("quality_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("readability_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("intent_validation_passed", sa.Boolean, nullable=True),
        sa.Column(
            "intent_validation_issues",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("featured_image_url", sa.String(500), nullable=True),
        sa.Column("featured_image_credit", sa.String(255), nullable=True),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column(
            "cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"
        ),
        sa.Column(
            "status",
            page_status_enum,
            nullable=False,
            server_default="draft",
        ),
        sa.Column("published_url", sa.String(500), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("generated_pages")
    op.drop_table("keywords")
    op.drop_table("campaigns")
    op.drop_table("prompt_templates")
    op.drop_table("site_contexts")
    op.drop_table("projects")
    op.execute("DROP TYPE page_status_enum")
    op.execute("DROP TYPE keyword_status_enum")
    op.execute("DROP TYPE campaign_status_enum")
    op.execute("DROP TYPE cms_type_enum")
