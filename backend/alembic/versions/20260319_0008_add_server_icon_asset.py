"""add server icon asset column

Revision ID: 20260319_0008
Revises: 20260319_0007
Create Date: 2026-03-19 15:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_0008"
down_revision = "20260319_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("servers", sa.Column("icon_asset", sa.String(length=255), nullable=True))

    bind = op.get_bind()
    icon_updates = {
        "Общая": "Общая.png",
        "Империя": "Империя.png",
        "Саммерсет": "Саммерсет.png",
        "Хай Рок": "Хай Рок.png",
        "Валенвуд": "Валенвуд.png",
        "Хаммерфелл": "Хаммерфелл.png",
        "Скайрим": "Скайрим.png",
        "Тельваннис": "Дом Тельванни.png",
        "Солтсхейм": "Дракон.png",
        "Эльсвеер": "Эльсвеер.png",
    }

    for server_name, icon_asset in icon_updates.items():
        bind.execute(
            sa.text(
                """
                UPDATE servers
                SET icon_asset = :icon_asset
                WHERE name = :server_name
                  AND icon_asset IS NULL
                """
            ),
            {"icon_asset": icon_asset, "server_name": server_name},
        )


def downgrade() -> None:
    op.drop_column("servers", "icon_asset")
