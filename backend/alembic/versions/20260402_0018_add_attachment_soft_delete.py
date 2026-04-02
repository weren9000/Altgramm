"""add attachment soft delete fields

Revision ID: 20260402_0018
Revises: 20260401_0017
Create Date: 2026-04-02 18:20:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0018"
down_revision = "20260401_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attachments", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("attachments", sa.Column("deleted_by_user_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_attachments_deleted_by_user_id_users",
        "attachments",
        "users",
        ["deleted_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_attachments_deleted_by_user_id_users", "attachments", type_="foreignkey")
    op.drop_column("attachments", "deleted_by_user_id")
    op.drop_column("attachments", "deleted_at")
