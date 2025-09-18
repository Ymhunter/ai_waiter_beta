from fastapi import WebSocket, WebSocketDisconnect
import asyncio

active_connections: list[WebSocket] = []

async def connect_ws(websocket: WebSocket):
    """Handle new WebSocket connections (chat + dashboard)."""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            try:
                # Wait for messages, but timeout so we can send heartbeats
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                print("📩 Received WS message:", msg)
            except asyncio.TimeoutError:
                # Send heartbeat every 30s to keep connection alive
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
            print("❌ WS disconnected")

async def broadcast_update(slots, bookings):
    """Send updated slots & bookings to all connected clients."""
    payload = {"slots": slots, "bookings": bookings}
    to_remove = []
    for ws in active_connections:
        try:
            await ws.send_json(payload)
        except Exception as e:
            print("⚠️ WS send failed:", e)
            to_remove.append(ws)
    for ws in to_remove:
        if ws in active_connections:
            active_connections.remove(ws)

def trigger_broadcast(slots, bookings):
    """Schedule broadcast without blocking API response."""
    asyncio.create_task(broadcast_update(slots, bookings))
