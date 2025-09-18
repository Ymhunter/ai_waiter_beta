import os
import requests
from fastapi import FastAPI, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from .routers import slots, bookings

app = FastAPI(title="AI Booking Backend")

# Routers
app.include_router(slots.router)
app.include_router(bookings.router)

# Serve static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "..", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PUBLIC_URL = "https://ai-waiter-beta.onrender.com"

# Tools
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

@app.get("/chat-ui")
def serve_chat():
    return FileResponse(os.path.join(STATIC_DIR, "chat.html"))

@app.get("/dashboard")
def serve_dashboard():
    return FileResponse(os.path.join(STATIC_DIR, "dashboard.html"))


@app.post("/chat")
def chat(user_input: dict = Body(...)):
    try:
        user_message = user_input.get("message", "")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a booking assistant."},
                {"role": "user", "content": user_message},
            ],
            tools=[{"type": "function", "function": fn} for fn in functions],
            tool_choice="auto"
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            tool_call = msg.tool_calls[0]
            fn_name = tool_call.function.name
            args = {}

            if tool_call.function.arguments and tool_call.function.arguments != "{}":
                try:
                    import json
                    args = json.loads(tool_call.function.arguments)
                except Exception:
                    args = {}

            if fn_name == "get_slots":
                slots_res = requests.get(f"{PUBLIC_URL}/slots/").json()
                return {"reply": f"Here are the available slots: {slots_res}"}

            if fn_name == "create_booking":
                booking_res = requests.post(f"{PUBLIC_URL}/bookings/", json=args).json()
                return {"reply": f"Booking confirmed ✅: {booking_res}"}

        return {"reply": msg.content}

    except Exception as e:
        return {"error": str(e)}
