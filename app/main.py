from fastapi import FastAPI, WebSocket, Depends
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from .routes import pages, intent, chat, slots, bookings, payment
from .database import get_db
from .websocket_manager import connect_ws
from .helpers import get_slots_sync, get_bookings_sync

app = FastAPI(title="Barbershop Booking AI Agent")
# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="SESSION_SECRET")

# ------------------------------
# Serve static files (CSS/JS)
# ------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ------------------------------
# Routers
# ------------------------------
app.include_router(pages.router)
app.include_router(intent.router)
app.include_router(chat.router)
app.include_router(slots.router)
app.include_router(bookings.router)
app.include_router(payment.router)

# ------------------------------
# WebSocket (shared for chat + dashboard)
# ------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await connect_ws(websocket)
