import os
import requests
from fastapi import FastAPI, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from .routers import slots, bookings

# Create FastAPI app
app = FastAPI(title="AI Booking Backend")

# Include routers
app.include_router(slots.router)
app.include_router(bookings.router)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Public URL of your deployed app
PUBLIC_URL = "https://ai-waiter-beta.onrender.com"

# Paths for frontend
BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

# Serve static files (CSS, JS, images)
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Functions that GPT can call
functions = [
    {
        "name": "get_slots",
        "description": "Get available booking slots",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "create_booking",
        "description": "Create a booking for a slot",
        "parameters": {
            "type": "object",
            "properties": {
                "slot_id": {"type": "integer"},
                "customer_name": {"type": "string"},
                "customer_email": {"type": "string"},
            },
            "required": ["slot_id", "customer_name", "customer_email"],
        },
    },
]

# Chat endpoint (API)
@app.post("/chat")
def chat(user_input: dict = Body(...)):
    user_message = user_input.get("message", "")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a booking assistant."},
            {"role": "user", "content": user_message},
        ],
    )

    msg = response.choices[0].message

    # Handle function calls
    if msg.get("function_call"):
        fn_name = msg.function_call.name
        args = eval(msg.function_call.arguments)

        if fn_name == "get_slots":
            slots_res = requests.get(f"{PUBLIC_URL}/slots/").json()
            return {"reply": f"Here are the available slots: {slots_res}"}

        if fn_name == "create_booking":
            booking_res = requests.post(
                f"{PUBLIC_URL}/bookings/", json=args
            ).json()
            return {"reply": f"Booking confirmed ✅: {booking_res}"}

    return {"reply": msg.get("content")}


# Serve Chat UI
@app.get("/chat")
def get_chat():
    return FileResponse(os.path.join(FRONTEND_DIR, "chat.html"))


# Serve Dashboard UI
@app.get("/dashboard")
def get_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))
