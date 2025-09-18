import os
from fastapi import FastAPI, WebSocket, Depends
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from .routes import pages, intent, chat, slots, bookings, payment, auth
from .database import get_db
from .websocket_manager import connect_ws

app = FastAPI(title="Barbershop Booking AI Agent")

# ------------------------------
# Session Middleware
# ------------------------------
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "CHANGE_ME_SECRET"))

# ------------------------------
# Serve static files (CSS/JS)
# ------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ------------------------------
# Routers
# ------------------------------
app.include_router(auth.router)      # 👈 add auth
app.include_router(pages.router)
app.include_router(intent.router)
app.include_router(chat.router)
app.include_router(slots.router)
app.include_router(bookings.router)
app.include_router(payment.router)

# ------------------------------
# WebSocket
# ------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await connect_ws(websocket)
