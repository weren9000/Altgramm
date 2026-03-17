"""Add voice channel type.

Revision ID: 20260317_0003
Revises: 20260317_0002
Create Date: 2026-03-17 12:20:00
"""

from __future__ import annotations

from alembic import op


revision = "20260317_0003"
down_revision = "20260317_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE channeltype ADD VALUE IF NOT EXISTS 'voice'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values in place.
    pass
