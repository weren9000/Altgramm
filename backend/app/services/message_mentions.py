from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ServerMember, User


def _is_boundary_char(char: str) -> bool:
    return not (char.isalnum() or char == "_")


def _has_boundary_at(content: str, index: int) -> bool:
    if index <= 0:
        return True

    return _is_boundary_char(content[index - 1])


def _has_boundary_after(content: str, index: int) -> bool:
    if index >= len(content):
        return True

    return _is_boundary_char(content[index])


def resolve_message_mention_user_ids(
    db: Session,
    server_id: UUID,
    content: str,
    *,
    author_user_id: UUID,
) -> list[UUID]:
    normalized_content = content.strip()
    if "@" not in normalized_content:
        return []

    member_rows = db.execute(
        select(User.id, User.public_id, User.username)
        .join(ServerMember, ServerMember.user_id == User.id)
        .where(ServerMember.server_id == server_id, User.id != author_user_id)
    ).all()
    if not member_rows:
        return []

    candidates_by_user_id: dict[UUID, set[str]] = {}
    for user_id, public_id, username in member_rows:
        user_candidates = candidates_by_user_id.setdefault(user_id, set())
        username_label = (username or "").strip()
        if username_label:
            user_candidates.add(f"@{username_label.casefold()}")
        if public_id is not None:
            user_candidates.add(f"@{int(public_id)}")

    ordered_candidates: list[tuple[UUID, str]] = sorted(
        (
            (user_id, token)
            for user_id, tokens in candidates_by_user_id.items()
            for token in tokens
        ),
        key=lambda item: len(item[1]),
        reverse=True,
    )
    if not ordered_candidates:
        return []

    content_folded = normalized_content.casefold()
    mentioned_user_ids: set[UUID] = set()

    search_from = 0
    while True:
        mention_start = content_folded.find("@", search_from)
        if mention_start < 0:
            break

        if not _has_boundary_at(normalized_content, mention_start):
            search_from = mention_start + 1
            continue

        for user_id, token in ordered_candidates:
            mention_end = mention_start + len(token)
            if not content_folded.startswith(token, mention_start):
                continue

            if not _has_boundary_after(normalized_content, mention_end):
                continue

            mentioned_user_ids.add(user_id)
            break

        search_from = mention_start + 1

    return list(mentioned_user_ids)


def message_mentions_user_id(message_mentioned_user_ids: Iterable[UUID], user_id: UUID) -> bool:
    return any(mentioned_user_id == user_id for mentioned_user_id in message_mentioned_user_ids)
