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
        # cleanup
        clean_expired_slots(db)
        clean_stale_bookings(db)

        # build slots info
        slots = get_slots_sync(db)
        future_slots = [f"{d} {t}" for d, times in slots.items() for t in times]
        slot_info = ", ".join(future_slots) if future_slots else "No slots available"

        # build messages
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a polite barbershop assistant. "
                    f"Available slots are: {slot_info}. "
                    "Collect customer name, date, and time. "
                    "If all present, respond ONLY with valid JSON using double quotes: "
                    '{"service":"Haircut","date":"YYYY-MM-DD","time":"HH:MM","customer_name":"NAME"}'
                ),
            }
        ]
        if user_input.history:
            messages.extend(user_input.history)
        messages.append({"role": "user", "content": user_input.message})

        # call OpenAI
        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = response.choices[0].message.content or ""

        # try to extract JSON
        booking_match = re.search(r"\{.*\}", reply, re.DOTALL)
        if booking_match:
            raw_json = booking_match.group()
            try:
                booking_data = json.loads(raw_json)
            except Exception:
                booking_data = ast.literal_eval(raw_json)

            # check if slot exists
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

            # create booking
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

            # 🔥 broadcast updates to dashboard
            updated_slots = get_slots_sync(db)
            updated_bookings = get_bookings_sync(db)
            await trigger_broadcast(updated_slots, updated_bookings)

            return {
                "status": "reserved",
                "reply": (
                    f"✅ Reserved! Booking ID: {booking_id} for {booking.customer_name} "
                    f"at {booking.time.strftime('%H:%M')} on {booking.date.isoformat()}.<br><br>💳 Pay now?"
                ),
                "booking_id": booking_id,
            }

        # normal reply
        return {"status": "ok", "reply": reply}

    except Exception as e:
        return {"status": "error", "reply": f"⚠️ Error: {str(e)}"}
