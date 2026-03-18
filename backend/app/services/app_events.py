from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from anyio import from_thread
from fastapi import WebSocket


def _normalize_user_id(user_id: UUID | str) -> str:
    return str(user_id)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AppEventManager:
    def __init__(self) -> None:
        self._connections: dict[str, dict[str, WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: UUID | str) -> str:
        connection_id = uuid4().hex
        normalized_user_id = _normalize_user_id(user_id)

        await websocket.accept()

        async with self._lock:
            user_connections = self._connections.setdefault(normalized_user_id, {})
            user_connections[connection_id] = websocket

        return connection_id

    async def disconnect(self, user_id: UUID | str, connection_id: str) -> None:
        normalized_user_id = _normalize_user_id(user_id)

        async with self._lock:
            user_connections = self._connections.get(normalized_user_id)
            if user_connections is None:
                return

            user_connections.pop(connection_id, None)
            if not user_connections:
                self._connections.pop(normalized_user_id, None)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            recipients = [
                (user_id, connection_id, websocket)
                for user_id, user_connections in self._connections.items()
                for connection_id, websocket in user_connections.items()
            ]

        await self._send_payload(recipients, payload)

    async def send_to_user(self, user_id: UUID | str, payload: dict[str, Any]) -> None:
        normalized_user_id = _normalize_user_id(user_id)

        async with self._lock:
            user_connections = self._connections.get(normalized_user_id, {})
            recipients = [
                (normalized_user_id, connection_id, websocket)
                for connection_id, websocket in user_connections.items()
            ]

        await self._send_payload(recipients, payload)

    async def send_to_users(self, user_ids: Iterable[UUID | str], payload: dict[str, Any]) -> None:
        normalized_user_ids = {_normalize_user_id(user_id) for user_id in user_ids}
        if not normalized_user_ids:
            return

        async with self._lock:
            recipients = [
                (user_id, connection_id, websocket)
                for user_id in normalized_user_ids
                for connection_id, websocket in self._connections.get(user_id, {}).items()
            ]

        await self._send_payload(recipients, payload)

    async def _send_payload(
        self,
        recipients: list[tuple[str, str, WebSocket]],
        payload: dict[str, Any],
    ) -> None:
        stale_connections: list[tuple[str, str]] = []

        for user_id, connection_id, websocket in recipients:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale_connections.append((user_id, connection_id))

        for user_id, connection_id in stale_connections:
            await self.disconnect(user_id, connection_id)


app_event_manager = AppEventManager()


def build_presence_updated_event(user_id: UUID | str, *, is_online: bool = True) -> dict[str, Any]:
    return {
        "type": "presence_updated",
        "user_id": _normalize_user_id(user_id),
        "is_online": is_online,
        "last_active_at": _utc_now_iso(),
    }


def build_message_created_event(
    server_id: UUID | str,
    message: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "message_created",
        "server_id": _normalize_user_id(server_id),
        "message": message,
    }


def build_servers_changed_event(*, reason: str) -> dict[str, Any]:
    return {
        "type": "servers_changed",
        "reason": reason,
    }


def build_server_changed_event(server_id: UUID | str, *, reason: str) -> dict[str, Any]:
    return {
        "type": "server_changed",
        "server_id": _normalize_user_id(server_id),
        "reason": reason,
    }


def build_voice_inbox_changed_event() -> dict[str, Any]:
    return {
        "type": "voice_inbox_changed",
    }


def build_voice_request_resolved_event(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "voice_request_resolved",
        "request": request,
    }


async def publish_presence_updated(user_id: UUID | str, is_online: bool = True) -> None:
    await app_event_manager.broadcast(build_presence_updated_event(user_id, is_online=is_online))


async def publish_message_created(server_id: UUID | str, message: dict[str, Any]) -> None:
    await app_event_manager.broadcast(build_message_created_event(server_id, message))


async def publish_servers_changed(reason: str) -> None:
    await app_event_manager.broadcast(build_servers_changed_event(reason=reason))


async def publish_server_changed(server_id: UUID | str, reason: str) -> None:
    await app_event_manager.broadcast(build_server_changed_event(server_id, reason=reason))


async def publish_voice_inbox_changed() -> None:
    await app_event_manager.broadcast(build_voice_inbox_changed_event())


async def publish_voice_request_resolved(user_id: UUID | str, request: dict[str, Any]) -> None:
    await app_event_manager.send_to_user(user_id, build_voice_request_resolved_event(request))


def publish_presence_updated_from_sync(user_id: UUID | str, *, is_online: bool = True) -> None:
    from_thread.run(publish_presence_updated, user_id, is_online)


def publish_servers_changed_from_sync(*, reason: str) -> None:
    from_thread.run(publish_servers_changed, reason)


def publish_server_changed_from_sync(server_id: UUID | str, *, reason: str) -> None:
    from_thread.run(publish_server_changed, server_id, reason)


def publish_voice_inbox_changed_from_sync() -> None:
    from_thread.run(publish_voice_inbox_changed)
