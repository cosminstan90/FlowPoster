"""add search_volume, keyword_difficulty, cpc_usd, source to keywords

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-23 00:00:02.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("keywords", sa.Column("search_volume", sa.Integer(), nullable=True))
    op.add_column("keywords", sa.Column("keyword_difficulty", sa.Integer(), nullable=True))
    op.add_column("keywords", sa.Column("cpc_usd", sa.Numeric(6, 2), nullable=True))
    op.add_column(
        "keywords",
        sa.Column("source", sa.String(50), nullable=False, server_default="manual"),
    )


def downgrade() -> None:
    op.drop_column("keywords", "source")
    op.drop_column("keywords", "cpc_usd")
    op.drop_column("keywords", "keyword_difficulty")
    op.drop_column("keywords", "search_volume")
