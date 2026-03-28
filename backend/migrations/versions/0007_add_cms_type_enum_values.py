"""add velocitycms and dreamcms to cms_type_enum

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-28
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE to add new enum values.
    # Each value is added with IF NOT EXISTS (PostgreSQL 9.6+) for idempotency.
    op.execute("ALTER TYPE cms_type_enum ADD VALUE IF NOT EXISTS 'velocitycms'")
    op.execute("ALTER TYPE cms_type_enum ADD VALUE IF NOT EXISTS 'dreamcms'")


def downgrade() -> None:
    # PostgreSQL does NOT support removing enum values natively.
    # To roll back: rename the old type, recreate it with the original values,
    # cast the column, then drop the renamed type.
    op.execute("""
        ALTER TYPE cms_type_enum RENAME TO cms_type_enum_old;

        CREATE TYPE cms_type_enum AS ENUM ('wordpress', 'php_custom');

        ALTER TABLE projects
            ALTER COLUMN cms_type TYPE cms_type_enum
            USING cms_type::text::cms_type_enum;

        DROP TYPE cms_type_enum_old;
    """)
