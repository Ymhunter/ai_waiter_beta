from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import asyncio

active_connections: list[WebSocket] = []

async def connect_ws(websocket: WebSocket):
    """Handle new WebSocket connections (chat + dashboard)."""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

async def broadcast_update(slots, bookings):
    """Send updated slots & bookings to all connected clients."""
    payload = {"slots": slots, "bookings": bookings}
    to_remove = []
    for ws in active_connections:
        try:
            await ws.send_json(payload)
        except Exception:
            to_remove.append(ws)
    for ws in to_remove:
        active_connections.remove(ws)

def trigger_broadcast(slots, bookings):
    """Schedule broadcast without blocking API response."""
    asyncio.create_task(broadcast_update(slots, bookings))
