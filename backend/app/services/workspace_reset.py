from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Channel, ChannelType, MemberRole, Server, ServerMember, User, VoiceAccessRole, VoiceChannelAccess
from app.services.default_tavern import ensure_default_tavern_access_for_users, ensure_default_tavern_channel
from app.services.server_icons import get_default_server_icon_asset


@dataclass(frozen=True)
class ServerBlueprint:
    name: str
    voice_channels: tuple[str, ...]


VOICE_CHANNELS_TEMPLATE = (
    "Кабинет Правителя",
    "Храм",
    "Премный зал",
    "Улицы",
    "Гильдия",
)

WORKSPACE_BLUEPRINT = (
    ServerBlueprint(name="Общая", voice_channels=()),
    ServerBlueprint(name="Империя", voice_channels=VOICE_CHANNELS_TEMPLATE),
    ServerBlueprint(name="Саммерсет", voice_channels=VOICE_CHANNELS_TEMPLATE),
    ServerBlueprint(name="Хай Рок", voice_channels=VOICE_CHANNELS_TEMPLATE),
    ServerBlueprint(name="Валенвуд", voice_channels=VOICE_CHANNELS_TEMPLATE),
    ServerBlueprint(name="Хаммерфелл", voice_channels=VOICE_CHANNELS_TEMPLATE),
    ServerBlueprint(name="Скайрим", voice_channels=VOICE_CHANNELS_TEMPLATE),
    ServerBlueprint(name="Тельваннис", voice_channels=VOICE_CHANNELS_TEMPLATE),
    ServerBlueprint(name="Солтсхейм", voice_channels=VOICE_CHANNELS_TEMPLATE),
    ServerBlueprint(name="Эльсвеер", voice_channels=VOICE_CHANNELS_TEMPLATE),
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[\W_]+", "-", value.casefold(), flags=re.UNICODE).strip("-")
    return slug or "group"


def _deduplicate_blueprint(blueprint: Sequence[ServerBlueprint]) -> list[ServerBlueprint]:
    unique_items: list[ServerBlueprint] = []
    seen_names: set[str] = set()
    for item in blueprint:
        if item.name in seen_names:
            continue
        seen_names.add(item.name)
        unique_items.append(item)
    return unique_items


def _pick_workspace_owner(users: Iterable[User]) -> User:
    settings = get_settings()
    user_list = list(users)
    if not user_list:
        raise RuntimeError("Нельзя пересобрать рабочее пространство без пользователей")

    preferred_login = settings.demo_login.strip().casefold()
    preferred_nick = settings.demo_nick.strip().casefold()

    for user in user_list:
        if user.email.casefold() == preferred_login or user.username.casefold() == preferred_nick:
            return user

    for user in user_list:
        if user.is_admin:
            return user

    return user_list[0]


def reset_workspace_to_blueprint(
    db: Session,
    blueprint: Sequence[ServerBlueprint] = WORKSPACE_BLUEPRINT,
) -> list[Server]:
    users = db.execute(select(User).order_by(User.created_at, User.id)).scalars().all()
    owner = _pick_workspace_owner(users)
    unique_blueprint = _deduplicate_blueprint(blueprint)

    db.execute(delete(Server))
    db.flush()

    created_servers: list[Server] = []
    tavern_channels: list[Channel] = []

    for blueprint_item in unique_blueprint:
        server = Server(
            name=blueprint_item.name,
            slug=_slugify(blueprint_item.name),
            description=None,
            icon_asset=get_default_server_icon_asset(blueprint_item.name),
            owner_id=owner.id,
        )
        db.add(server)
        db.flush()
        created_servers.append(server)

        for user in users:
            role = MemberRole.OWNER if user.id == owner.id else MemberRole.MEMBER
            nickname = user.username if user.id != owner.id else None
            db.add(
                ServerMember(
                    server_id=server.id,
                    user_id=user.id,
                    role=role,
                    nickname=nickname,
                )
            )

        for position, voice_channel_name in enumerate(blueprint_item.voice_channels):
            channel = Channel(
                server_id=server.id,
                created_by_id=owner.id,
                name=voice_channel_name,
                topic=None,
                type=ChannelType.VOICE,
                position=position,
            )
            db.add(channel)
            db.flush()

            for user in users:
                role = VoiceAccessRole.OWNER if user.id == owner.id else VoiceAccessRole.RESIDENT
                db.add(
                    VoiceChannelAccess(
                        channel_id=channel.id,
                        user_id=user.id,
                        role=role,
                    )
                )

        tavern_channel = ensure_default_tavern_channel(db, server, created_by_id=owner.id)
        tavern_channels.append(tavern_channel)

    ensure_default_tavern_access_for_users(db, tavern_channels, users)
    db.commit()

    for server in created_servers:
        db.refresh(server)

    return created_servers
