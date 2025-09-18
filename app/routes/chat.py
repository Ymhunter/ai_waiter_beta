import re, json, uuid, ast
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models import ChatMessage
from ..deps import get_db
from ..helpers import clean_expired_slots, clean_stale_bookings, get_slots_sync, get_bookings_sync
from ..config import client
from ..database import Booking, Slot, to_date, to_time
from ..websocket_manager import trigger_broadcast

router = APIRouter()

@router.post("/chat")
async def chat_with_agent(user_input: ChatMessage, db: Session = Depends(get_db)):
    try:
        clean_expired_slots(db)
        clean_stale_bookings(db)
        slots = get_slots_sync(db)
        future_slots = [f"{d} {t}" for d, times in slots.items() for t in times]
        slot_info = ", ".join(future_slots) if future_slots else "No slots available"

        # ✅ Force assistant to always return valid JSON with double quotes
        messages = [
            {"role": "system", "content": f"""
You are a polite barbershop assistant. 
Available slots are: {slot_info}.

Your task:
- Collect the customer's name
- Collect a valid available date (YYYY-MM-DD)
- Collect a valid available time (HH:MM)

❗ Rules:
- If the user already gave all three (name, date, time), respond ONLY with valid JSON:
{{"service":"Haircut","date":"YYYY-MM-DD","time":"HH:MM","customer_name":"NAME"}}
- Use double quotes around all keys and string values.
- Do NOT add any extra words, explanations, or formatting.
- If something is missing, only ask for that missing part.
"""}
        ]
        if user_input.history:
            messages.extend(user_input.history)
        messages.append({"role": "user", "content": user_input.message})

        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = response.choices[0].message.content or ""

        booking_match = re.search(r"\{.*?\}", reply, re.DOTALL)
        if booking_match:
            raw_json = booking_match.group()
            try:
                booking_data = json.loads(raw_json)  # strict JSON
            except json.JSONDecodeError:
                # fallback if GPT slips and uses single quotes
                booking_data = ast.literal_eval(raw_json)

            slot_exists = db.query(Slot).filter_by(
                date=to_date(booking_data["date"]),
                time=to_time(booking_data["time"]),
                available=True
            ).first()
            if not slot_exists:
                return {"status": "unavailable", "reply": "❌ Sorry, that slot is not available."}

            booking_id = str(uuid.uuid4())
            booking = Booking(
                id=booking_id,
                customer_name=booking_data["customer_name"],
                service=booking_data["service"],
                date=to_date(booking_data["date"]),
                time=to_time(booking_data["time"]),
                status="pending"
            )
            db.add(booking)
            slot_exists.available = False
            db.commit()

            # 🔥 fix: broadcast update properly
            slots = get_slots_sync(db)
            bookings = get_bookings_sync(db)
            await trigger_broadcast(slots, bookings)

            return {
                "status": "reserved",
                "reply": f"✅ Reserved! Booking ID: {booking_id} for {booking.customer_name} "
                        f"at {booking.time.strftime('%H:%M')} on {booking.date.isoformat()}.<br><br>💳 Pay now?",
                "booking_id": booking_id
            }

