"""drop legacy user profile fields

Revision ID: 20260331_0014
Revises: 20260331_0013
Create Date: 2026-03-31 21:45:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260331_0014"
down_revision = "20260331_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("users", "bio")
    op.drop_column("users", "display_name")


def downgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=64), nullable=False, server_default=""))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.alter_column("users", "display_name", server_default=None)
