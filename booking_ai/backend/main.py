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

        # 🔍 Debug: return raw tool_calls
        if msg.tool_calls:
            return {"raw_tool_calls": [tc.dict() for tc in msg.tool_calls]}

        return {"reply": msg.content}

    except Exception as e:
        return {"error": str(e)}
