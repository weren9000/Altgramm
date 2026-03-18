from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.api.dependencies.auth import resolve_user_from_token
from app.db.session import SessionLocal
from app.services.app_events import app_event_manager, build_presence_updated_event
from app.services.site_presence import site_presence_manager

router = APIRouter(prefix="/events", tags=["events"])


@router.websocket("/ws")
async def connect_app_events(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401, reason="Missing token")
        return

    with SessionLocal() as db:
        try:
            current_user = resolve_user_from_token(token, db)
        except HTTPException:
            await websocket.close(code=4401, reason="Unauthorized")
            return

    connection_id = await app_event_manager.connect(websocket, current_user.id)
    site_presence_manager.mark_active(current_user.id)
    await websocket.send_json(
        {
            "type": "ready",
            "user_id": str(current_user.id),
        }
    )
    await app_event_manager.broadcast(build_presence_updated_event(current_user.id))

    try:
        while True:
            payload = await websocket.receive_json()
            message_type = payload.get("type")

            if message_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if message_type == "activity":
                site_presence_manager.mark_active(current_user.id)
                await app_event_manager.broadcast(build_presence_updated_event(current_user.id))
                continue

            await websocket.send_json(
                {
                    "type": "error",
                    "detail": f"Unsupported event message: {message_type!r}",
                }
            )
    except WebSocketDisconnect:
        pass
    finally:
        await app_event_manager.disconnect(current_user.id, connection_id)
