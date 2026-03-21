"""add praying cat reaction

Revision ID: 20260321_0010
Revises: 20260320_0009
Create Date: 2026-03-21 10:20:00
"""

from __future__ import annotations

from alembic import op


revision = "20260321_0010"
down_revision = "20260320_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE messagereactionkind ADD VALUE IF NOT EXISTS 'praying_cat'")


def downgrade() -> None:
    # PostgreSQL enum values are not removed automatically on downgrade.
    pass
