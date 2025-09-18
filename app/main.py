from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import pages, intent, chat, slots, bookings, payment
from .websocket_manager import dashboard_ws

app = FastAPI(title="Barbershop Booking AI Agent")

# Serve static files (CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(pages.router)
app.include_router(intent.router)
app.include_router(chat.router)
app.include_router(slots.router)
app.include_router(bookings.router)
app.include_router(payment.router)

# WebSocket
app.websocket("/ws/dashboard")(dashboard_ws)
