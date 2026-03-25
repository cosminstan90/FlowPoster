"""add geo fields to campaigns and generated_pages

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-25
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # campaigns
    op.add_column("campaigns", sa.Column("geo_enabled", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("campaigns", sa.Column("geo_mode", sa.String(50), nullable=False, server_default="balanced"))

    # generated_pages
    op.add_column("generated_pages", sa.Column("geo_score", sa.Integer, nullable=True))
    op.add_column("generated_pages", sa.Column("geo_breakdown", sa.JSON, nullable=True))
    op.add_column("generated_pages", sa.Column("speakable_sections", sa.JSON, nullable=True))
    op.add_column("generated_pages", sa.Column("geo_version", sa.String(10), nullable=True))
    op.add_column("generated_pages", sa.Column("has_direct_answer", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("generated_pages", sa.Column("has_comparison_table", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("generated_pages", sa.Column("citation_density", sa.Numeric(4, 2), nullable=True))


def downgrade() -> None:
    # generated_pages
    op.drop_column("generated_pages", "citation_density")
    op.drop_column("generated_pages", "has_comparison_table")
    op.drop_column("generated_pages", "has_direct_answer")
    op.drop_column("generated_pages", "geo_version")
    op.drop_column("generated_pages", "speakable_sections")
    op.drop_column("generated_pages", "geo_breakdown")
    op.drop_column("generated_pages", "geo_score")

    # campaigns
    op.drop_column("campaigns", "geo_mode")
    op.drop_column("campaigns", "geo_enabled")
