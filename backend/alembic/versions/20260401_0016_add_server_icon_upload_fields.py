"""add server icon upload fields

Revision ID: 20260401_0016
Revises: 20260331_0015
Create Date: 2026-04-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_0016"
down_revision = "20260331_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("servers", sa.Column("icon_filename", sa.String(length=255), nullable=True))
    op.add_column("servers", sa.Column("icon_mime_type", sa.String(length=128), nullable=True))
    op.add_column("servers", sa.Column("icon_size_bytes", sa.Integer(), nullable=True))
    op.add_column("servers", sa.Column("icon_content", sa.LargeBinary(), nullable=True))
    op.add_column("servers", sa.Column("icon_updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("servers", "icon_updated_at")
    op.drop_column("servers", "icon_content")
    op.drop_column("servers", "icon_size_bytes")
    op.drop_column("servers", "icon_mime_type")
    op.drop_column("servers", "icon_filename")
