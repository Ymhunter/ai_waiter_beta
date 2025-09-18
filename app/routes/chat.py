import re, json, uuid, ast
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..models import ChatMessage
from ..deps import get_db
from ..config import client
from ..database import Booking, Slot, to_date, to_time
from ..helpers import (
    clean_expired_slots,
    clean_stale_bookings,
    get_slots_sync,
    get_bookings_sync,   # ← make sure this is imported
)
from ..websocket_manager import trigger_broadcast

router = APIRouter()


@router.post("/chat")
async def chat_with_agent(user_input: ChatMessage, db: Session = Depends(get_db)):
    try:
        # housekeeping
        clean_expired_slots(db)
        clean_stale_bookings(db)

        # build available slots summary for the prompt
        slots_now = get_slots_sync(db)
        future_slots = [f"{d} {t}" for d, times in slots_now.items() for t in times]
        slot_info = ", ".join(future_slots) if future_slots else "No slots available"

        # system prompt: force valid double-quoted JSON when all info present
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a polite barbershop assistant. "
                    f"Available slots are: {slot_info}.\n\n"
                    "Your task:\n"
                    "- Collect the customer's name\n"
                    "- Collect a valid available date (YYYY-MM-DD)\n"
                    "- Collect a valid available time (HH:MM)\n\n"
                    "Rules:\n"
                    '- If the user already gave all three (name, date, time), respond ONLY with valid JSON:\n'
                    '{"service":"Haircut","date":"YYYY-MM-DD","time":"HH:MM","customer_name":"NAME"}\n'
                    "- Use double quotes for all keys and string values.\n"
                    "- Do NOT add any extra words or formatting. If something is missing, only ask for that piece."
                ),
            }
        ]
        if user_input.history:
            messages.extend(user_input.history)
        messages.append({"role": "user", "content": user_input.message})

        # call OpenAI
        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = (response.choices[0].message.content or "").strip()

        # try to extract a JSON object from the reply
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if match:
            raw_json = match.group()
            try:
                booking_data = json.loads(raw_json)  # strict JSON first
            except json.JSONDecodeError:
                # fallback if the model used single quotes etc.
                booking_data = ast.literal_eval(raw_json)

            # verify slot availability
            slot_exists = (
                db.query(Slot)
                .filter_by(
                    date=to_date(booking_data["date"]),
                    time=to_time(booking_data["time"]),
                    available=True,
                )
                .first()
            )
            if not slot_exists:
                return {"status": "unavailable", "reply": "❌ Sorry, that slot is not available."}

            # create booking and mark slot unavailable
            booking_id = str(uuid.uuid4())
            booking = Booking(
                id=booking_id,
                customer_name=booking_data["customer_name"],
                service=booking_data["service"],
                date=to_date(booking_data["date"]),
                time=to_time(booking_data["time"]),
                status="pending",
            )
            db.add(booking)
            slot_exists.available = False
            db.commit()

            # broadcast latest state to all dashboards
            updated_slots = get_slots_sync(db)
            updated_bookings = get_bookings_sync(db)
            trigger_broadcast(updated_slots, updated_bookings)  # ← no await

            return {
                "status": "reserved",
                "reply": (
                    f"✅ Reserved! Booking ID: {booking_id} for {booking.customer_name} "
                    f"at {booking.time.strftime('%H:%M')} on {booking.date.isoformat()}.<br><br>💳 Pay now?"
                ),
                "booking_id": booking_id,
            }

        # otherwise, just relay the assistant’s reply (e.g., asking for missing info)
        return {"status": "ok", "reply": reply}

    except Exception as e:
        return {"status": "error", "reply": f"⚠️ Error: {str(e)}"}
