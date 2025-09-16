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
    message = user_input["message"]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful booking assistant. Use the available functions to check slots and make bookings."},
            {"role": "user", "content": message}
        ],
        functions=functions,
        function_call="auto"
    )

    msg = response.choices[0].message

    if msg.get("function_call"):
        fn_name = msg.function_call.name
        args = eval(msg.function_call.arguments)

        if fn_name == "get_slots":
            slots_res = requests.get(f"{PUBLIC_URL}/slots/").json()
            return {"reply": f"Here are the available slots: {slots_res}"}

        if fn_name == "create_booking":
            booking_res = requests.post(f"{PUBLIC_URL}/bookings/", json=args).json()
            return {"reply": f"Booking confirmed ✅: {booking_res}"}

    return {"reply": msg.content}
