import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from .helpers import get_slots_sync, get_bookings_sync

active_connections: list[WebSocket] = []

async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_update(db: Session):
    slots = get_slots_sync(db)
    bookings = get_bookings_sync(db)
    payload = {"slots": slots, "bookings": bookings}
    to_remove = []
    for ws in active_connections:
        try:
            await ws.send_json(payload)
        except Exception:
            to_remove.append(ws)
    for ws in to_remove:
        active_connections.remove(ws)

def trigger_broadcast(db: Session):
    asyncio.create_task(broadcast_update(db))
