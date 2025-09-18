import os
import requests
from fastapi import FastAPI, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from .routers import slots, bookings

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
app = FastAPI(title="AI Booking Backend")

# Include routers
app.include_router(slots.router)
app.include_router(bookings.router)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Public URL for API calls (adjust if your Render app changes)
PUBLIC_URL = "https://ai-waiter-beta.onrender.com"

# -----------------------------------------------------------------------------
# Mount frontend
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "../frontend"))

# Serve static files (CSS, JS, images if any)
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")

# Serve HTML pages
@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "chatbot.html"))

@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

# -----------------------------------------------------------------------------
# OpenAI function definitions
# -----------------------------------------------------------------------------
functions = [
    {
        "name": "get_slots",
        "description": "Get available booking slots",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "create_booking",
        "description": "Create a booking for a slot",
        "parameters": {
            "type": "object",
            "properties": {
                "slot_id": {"type": "integer"},
                "customer_name": {"type": "string"},
                "customer_email": {"type": "string"}
            },
            "required": ["slot_id", "customer_name", "customer_email"]
        }
    }
]

# -----------------------------------------------------------------------------
# Chat endpoint
# -----------------------------------------------------------------------------
@app.post("/chat")
def chat(user_input: dict = Body(...)):
    try:
        message = user_input.get("message", "")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a restaurant booking assistant."},
                {"role": "user", "content": message},
            ],
            tools=functions,
        )

        msg = response.choices[0].message

        # Handle tool calls (function calls)
        if msg.tool_calls:
            for tool in msg.tool_calls:
                fn_name = tool.function.name
                args = eval(tool.function.arguments)

                if fn_name == "get_slots":
                    slots_res = requests.get(f"{PUBLIC_URL}/slots/").json()
                    return {"reply": f"Here are the available slots: {slots_res}"}

                if fn_name == "create_booking":
                    booking_res = requests.post(f"{PUBLIC_URL}/bookings/", json=args).json()
                    return {"reply": f"Booking confirmed ✅: {booking_res}"}

        # Normal text reply
        return {"reply": msg.content}

    except Exception as e:
        # Always return JSON errors so frontend doesn’t break
        return {"error": str(e)}
