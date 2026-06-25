"""
WebSocket endpoint — fallback for clients that cannot use LiveKit data channels.
Broadcasts agent state updates (transcript lines, tool events, summary) over plain WS.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manage active WebSocket connections per room."""

    def __init__(self) -> None:
        # room_name -> list[WebSocket]
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_name: str) -> None:
        await websocket.accept()
        self._connections.setdefault(room_name, []).append(websocket)
        logger.info("ws_connected", room=room_name, total=len(self._connections[room_name]))

    def disconnect(self, websocket: WebSocket, room_name: str) -> None:
        conns = self._connections.get(room_name, [])
        if websocket in conns:
            conns.remove(websocket)
        logger.info("ws_disconnected", room=room_name, remaining=len(conns))

    async def broadcast(self, room_name: str, payload: dict[str, Any]) -> None:
        conns = self._connections.get(room_name, [])
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room_name)

    async def broadcast_all(self, payload: dict[str, Any]) -> None:
        for room_name in list(self._connections.keys()):
            await self.broadcast(room_name, payload)


# Singleton used by routes
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, room_name: str) -> None:
    """Accept a WS connection and keep it alive; relay pings."""
    await manager.connect(websocket, room_name)
    try:
        while True:
            # Keep-alive: just drain any incoming messages (client can send pings)
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except (WebSocketDisconnect, asyncio.TimeoutError):
        manager.disconnect(websocket, room_name)
    except Exception as exc:
        logger.error("ws_error", room=room_name, error=str(exc))
        manager.disconnect(websocket, room_name)
