"""add hot path indexes for memberships and attachments

Revision ID: 20260319_0007
Revises: 20260318_0006
Create Date: 2026-03-19 12:10:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "20260319_0007"
down_revision = "20260318_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_server_members_user_id", "server_members", ["user_id"], unique=False)
    op.create_index("ix_attachments_message_id", "attachments", ["message_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_attachments_message_id", table_name="attachments")
    op.drop_index("ix_server_members_user_id", table_name="server_members")
