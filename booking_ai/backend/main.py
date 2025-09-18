import os
import requests
from fastapi import FastAPI, Body
from openai import OpenAI

from .routers import slots, bookings

app = FastAPI(title="AI Booking Backend")
app.include_router(slots.router)
app.include_router(bookings.router)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PUBLIC_URL = "https://ai-waiter-beta.onrender.com"

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

@app.post("/chat")
def chat(user_input: dict = Body(...)):
    # Send user input to GPT
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a booking assistant."},
            {"role": "user", "content": user_input.get("message", "")},
        ]
    )

    # Get the assistant’s reply
    msg = response.choices[0].message

    # Handle function calls (new API style)
    if "function_call" in msg:
        fn_name = msg["function_call"]["name"]
        args = eval(msg["function_call"]["arguments"])

        if fn_name == "get_slots":
            slots_res = requests.get(f"{PUBLIC_URL}/slots/").json()
            return {"reply": f"Here are the available slots: {slots_res}"}

        if fn_name == "create_booking":
            booking_res = requests.post(f"{PUBLIC_URL}/bookings/", json=args).json()
            return {"reply": f"Booking confirmed ✅: {booking_res}"}

    # Default: return assistant’s text
    return {"reply": msg.get("content", "")}