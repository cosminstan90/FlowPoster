"""add summary_html to generated_pages

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-01
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generated_pages",
        sa.Column("summary_html", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generated_pages", "summary_html")
