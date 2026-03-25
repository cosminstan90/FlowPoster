"""add cluster_id and cluster_role to keywords

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-25 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("keywords", sa.Column("cluster_id", UUID(as_uuid=True), nullable=True))
    op.add_column("keywords", sa.Column("cluster_role", sa.String(20), nullable=True))
    op.create_index("ix_keywords_cluster_id", "keywords", ["cluster_id"])


def downgrade() -> None:
    op.drop_index("ix_keywords_cluster_id", table_name="keywords")
    op.drop_column("keywords", "cluster_role")
    op.drop_column("keywords", "cluster_id")
