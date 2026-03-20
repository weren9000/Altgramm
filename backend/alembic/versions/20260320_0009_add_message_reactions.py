"""add message reactions

Revision ID: 20260320_0009
Revises: 20260319_0008
Create Date: 2026-03-20 12:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260320_0009"
down_revision = "20260319_0008"
branch_labels = None
depends_on = None


message_reaction_kind = postgresql.ENUM(
    "heart",
    "like",
    "dislike",
    "angry",
    "cry",
    "confused",
    "displeased",
    "laugh",
    "fire",
    "wow",
    name="messagereactionkind",
    create_type=False,
)


def upgrade() -> None:
    message_reaction_kind.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "message_reactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("reaction", message_reaction_kind, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", "reaction", name="uq_message_reactions_message_user_reaction"),
    )
    op.create_index(
        "ix_message_reactions_message_reaction",
        "message_reactions",
        ["message_id", "reaction"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_message_reactions_message_reaction", table_name="message_reactions")
    op.drop_table("message_reactions")
    message_reaction_kind.drop(op.get_bind(), checkfirst=True)
