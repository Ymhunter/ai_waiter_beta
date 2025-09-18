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

# Mount frontend files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "chatbot.html"))

@app.get("/dashboard")
def dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

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

        # If AI wants to call a function
        if msg.get("tool_calls"):
            tool = msg["tool_calls"][0]
            fn_name = tool["function"]["name"]
            args = eval(tool["function"]["arguments"])

            if fn_name == "get_slots":
                slots_res = requests.get(f"{PUBLIC_URL}/slots/").json()
                return {"reply": f"Here are the available slots: {slots_res}"}

            if fn_name == "create_booking":
                booking_res = requests.post(f"{PUBLIC_URL}/bookings/", json=args).json()
                return {"reply": f"Booking confirmed ✅: {booking_res}"}

        # Otherwise return plain reply
        return {"reply": msg.get("content")}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
