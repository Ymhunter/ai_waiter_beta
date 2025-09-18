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

    
@app.post("/chat")
def chat(user_input: dict = Body(...)):
    message = user_input.get("message", "")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a restaurant booking assistant."},
            {"role": "user", "content": message},
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_slots",
                    "description": "Get available booking slots",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
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
            },
        ]
    )

    msg = response.choices[0].message

    # If GPT calls a function
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

    # Otherwise return GPT text
    return {"reply": msg.content}
