"""add message mentions

Revision ID: 20260415_0023
Revises: 20260410_0022
Create Date: 2026-04-15 10:30:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260415_0023"
down_revision = "20260410_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "message_mentions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_message_mentions_message_user"),
    )
    op.create_index("ix_message_mentions_user_id", "message_mentions", ["user_id"], unique=False)
    op.create_index("ix_message_mentions_message_id", "message_mentions", ["message_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_message_mentions_message_id", table_name="message_mentions")
    op.drop_index("ix_message_mentions_user_id", table_name="message_mentions")
    op.drop_table("message_mentions")
