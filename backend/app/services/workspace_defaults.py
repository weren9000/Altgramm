from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Channel, ChannelType, Server, ServerKind, ServerMember, User
from app.services.default_tavern import ensure_default_tavern_access_for_users, ensure_default_tavern_channel

DEFAULT_WORKSPACE_TEXT_NAME = "Общий чат"
DEFAULT_WORKSPACE_TEXT_TOPIC = "Главный текстовый канал площадки"


def ensure_workspace_text_channel(
    db: Session,
    server: Server,
    *,
    created_by_id: UUID,
) -> Channel:
    if server.kind != ServerKind.WORKSPACE:
        raise ValueError("Workspace defaults apply only to workspace servers")

    channel = db.execute(
        select(Channel)
        .where(Channel.server_id == server.id, Channel.type == ChannelType.TEXT)
        .order_by(Channel.position, Channel.name)
    ).scalars().first()

    if channel is not None:
        if not channel.topic:
            channel.topic = DEFAULT_WORKSPACE_TEXT_TOPIC
        return channel

    channel = Channel(
        server_id=server.id,
        created_by_id=created_by_id,
        name=DEFAULT_WORKSPACE_TEXT_NAME,
        topic=DEFAULT_WORKSPACE_TEXT_TOPIC,
        type=ChannelType.TEXT,
        position=0,
    )
    db.add(channel)
    db.flush()
    return channel


def ensure_workspace_defaults(
    db: Session,
    server: Server,
    *,
    created_by_id: UUID | None = None,
) -> tuple[Channel, Channel]:
    if server.kind != ServerKind.WORKSPACE:
        raise ValueError("Workspace defaults apply only to workspace servers")

    effective_created_by_id = created_by_id or server.owner_id
    text_channel = ensure_workspace_text_channel(db, server, created_by_id=effective_created_by_id)
    tavern_channel = ensure_default_tavern_channel(db, server, created_by_id=effective_created_by_id)
    members = db.execute(
        select(User)
        .join(ServerMember, ServerMember.user_id == User.id)
        .where(ServerMember.server_id == server.id)
        .order_by(ServerMember.joined_at, User.created_at, User.id)
    ).scalars().all()
    ensure_default_tavern_access_for_users(db, [tavern_channel], members)
    return text_channel, tavern_channel


def ensure_workspace_defaults_for_all(db: Session) -> None:
    servers = db.execute(
        select(Server).where(Server.kind == ServerKind.WORKSPACE).order_by(Server.created_at, Server.id)
    ).scalars().all()
    if not servers:
        return

    for server in servers:
        ensure_workspace_defaults(db, server, created_by_id=server.owner_id)
