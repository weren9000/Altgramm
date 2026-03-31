"""add message replies and channel read state

Revision ID: 20260331_0012
Revises: 20260321_0011
Create Date: 2026-03-31 12:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260331_0012"
down_revision = "20260321_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("reply_to_message_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_messages_reply_to_message_id_messages",
        "messages",
        "messages",
        ["reply_to_message_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "channel_read_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("last_read_message_id", sa.Uuid(), nullable=True),
        sa.Column("last_read_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["last_read_message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_id", "user_id", name="uq_channel_read_states_channel_user"),
    )
    op.create_index("ix_channel_read_states_user_id", "channel_read_states", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_channel_read_states_user_id", table_name="channel_read_states")
    op.drop_table("channel_read_states")
    op.drop_constraint("fk_messages_reply_to_message_id_messages", "messages", type_="foreignkey")
    op.drop_column("messages", "reply_to_message_id")
