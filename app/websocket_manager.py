from fastapi import WebSocket, WebSocketDisconnect
import asyncio

active_connections: list[WebSocket] = []

async def connect_ws(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            try:
                # Wait for a message with a timeout
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
async def broadcast_update(slots, bookings):
    print(f"📡 Broadcasting update: {len(active_connections)} connections")
    payload = {"slots": slots, "bookings": bookings}
    to_remove = []
    for ws in active_connections:
        try:
            await ws.send_json(payload)
            print("✅ Sent update to client")
        except Exception as e:
            print("❌ Failed to send update:", e)
            to_remove.append(ws)
    for ws in to_remove:
        active_connections.remove(ws)


def trigger_broadcast(slots, bookings):
    """Schedule broadcast without blocking API response."""
    asyncio.create_task(broadcast_update(slots, bookings))
