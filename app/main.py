from fastapi import FastAPI, WebSocket, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .routes import pages, intent, chat, slots, bookings, payment
from .database import get_db
from .websocket_manager import connect_ws

app = FastAPI(title="Barbershop Booking AI Agent")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(pages.router)
app.include_router(intent.router)
app.include_router(chat.router)
app.include_router(slots.router)
app.include_router(bookings.router)
app.include_router(payment.router)

# WebSocket for dashboard
@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    await connect_ws(websocket)

# WebSocket for chat
@app.websocket("/ws")
async def chat_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    await connect_ws(websocket)
