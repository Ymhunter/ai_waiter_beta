import re, json, uuid, ast
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from ..models import ChatMessage
from ..deps import get_db
from ..config import client
from ..database import Booking, Slot, to_date, to_time
from ..helpers import (
    clean_expired_slots,
    clean_stale_bookings,
    get_slots_sync,
    get_bookings_sync,
)
from ..websocket_manager import trigger_broadcast
from ..email_utils import send_email

router = APIRouter()


@router.post("/chat")
async def chat_with_agent(
    user_input: ChatMessage,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = Depends()
):
    try:
        # ------------------------------
        # Housekeeping
        # ------------------------------
        clean_expired_slots(db)
        clean_stale_bookings(db)

        # Build slots summary for assistant
        slots_now = get_slots_sync(db)
        future_slots = [f"{d} {t}" for d, times in slots_now.items() for t in times]
        slot_info = ", ".join(future_slots) if future_slots else "No slots available"

        # ------------------------------
        # Prompt setup
        # ------------------------------
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a polite barbershop assistant. "
                    f"Available slots are: {slot_info}.\n\n"
                    "Your task:\n"
                    "- Collect the customer's name\n"
                    "- Collect the customer's email\n"
                    "- Collect a valid available date (YYYY-MM-DD)\n"
                    "- Collect a valid available time (HH:MM)\n\n"
                    "Rules:\n"
                    '- If the user already gave all four (name, email, date, time), respond ONLY with valid JSON:\n'
                    '{"service":"Haircut","date":"YYYY-MM-DD","time":"HH:MM","customer_name":"NAME","customer_email":"EMAIL"}\n'
                    "- Use double quotes for all keys and string values.\n"
                    "- Do NOT add any extra words or formatting. If something is missing, only ask for that piece."
                ),
            }
        ]
        if user_input.history:
            messages.extend(user_input.history)
        messages.append({"role": "user", "content": user_input.message})

        # ------------------------------
        # Call OpenAI
        # ------------------------------
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply = (response.choices[0].message.content or "").strip()

        # ------------------------------
        # Try to extract booking JSON
        # ------------------------------
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if match:
            raw_json = match.group()
            try:
                booking_data = json.loads(raw_json)
            except json.JSONDecodeError:
                booking_data = ast.literal_eval(raw_json)

            # Verify slot exists & is available
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
                return {
                    "status": "unavailable",
                    "reply": "❌ Sorry, that slot is not available."
                }

            # ------------------------------
            # Create booking
            # ------------------------------
            booking_id = str(uuid.uuid4())
            booking = Booking(
                id=booking_id,
                customer_name=booking_data["customer_name"],
                service=booking_data["service"],
                date=to_date(booking_data["date"]),
                time=to_time(booking_data["time"]),
                status="pending",
                customer_email=booking_data.get("customer_email"),
            )
            db.add(booking)
            slot_exists.available = False
            db.commit()
            db.refresh(booking)

            print(f"📩 Booking saved: {booking.id}, {booking.customer_email}")

            # ------------------------------
            # Broadcast to dashboard
            # ------------------------------
            updated_slots = get_slots_sync(db)
            updated_bookings = get_bookings_sync(db)
            trigger_broadcast(updated_slots, updated_bookings)

            # ------------------------------
            # Send confirmation email
            # ------------------------------
            if booking.customer_email:
                subject = "Your Barbershop Appointment Confirmation"
                html = f"""
                <h2>Hi {booking.customer_name},</h2>
                <p>Your {booking.service} is booked for 
                {booking.date} at {booking.time.strftime('%H:%M')}.</p>
                <p>We look forward to seeing you! 💈</p>
                """
                background_tasks.add_task(
                    send_email,
                    booking.customer_email,
                    subject,
                    html
                )
                print(f"📧 Email queued for {booking.customer_email}")

            return {
                "status": "reserved",
                "reply": (
                    f"✅ Reserved! Booking ID: {booking_id} for {booking.customer_name} "
                    f"at {booking.time.strftime('%H:%M')} on {booking.date.isoformat()}."
                ),
                "booking_id": booking_id,
            }

        # ------------------------------
        # No JSON → just ask for missing info
        # ------------------------------
        return {"status": "ok", "reply": reply}

    except Exception as e:
        print("❌ Chat error:", e)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
