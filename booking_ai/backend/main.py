import os
import requests
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from .routers import slots, bookings

# Initialize FastAPI
app = FastAPI(title="AI Booking Backend")

# Include API routers
app.include_router(slots.router)
app.include_router(bookings.router)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Public URL for function calls
PUBLIC_URL = "https://ai-waiter-beta.onrender.com"

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")

# ✅ Serve frontend HTML files directly
@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "chatbot.html"))

@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

# ✅ Optional: if you later add static assets (CSS, JS, images)
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Chat endpoint
@app.post("/chat")
def chat(payload: dict = Body(...)):
    user_message = payload.get("message")
    if not user_message:
        return JSONResponse(status_code=400, content={"error": "Message is required"})

    try:
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a booking assistant."},
                {"role": "user", "content": user_message},
            ],
        )

        # ✅ Access attributes instead of using .get()
        msg = response.choices[0].message
        return {"reply": msg.content}   # <-- fixed

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
