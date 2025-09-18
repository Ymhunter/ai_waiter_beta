from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import Booking, Slot, get_db
from ..helpers import get_slots_sync, get_bookings_sync
from ..websocket_manager import trigger_broadcast

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

# Get all bookings
@router.get("")
async def get_bookings(db: Session = Depends(get_db)):
    return get_bookings_sync(db)

# Cancel a booking
@router.post("/{booking_id}/cancel")
async def cancel_booking(booking_id: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = "cancelled"
    slot = db.query(Slot).filter_by(date=booking.date, time=booking.time).first()
    if slot:
        slot.available = True

    db.commit()

    # 👇 broadcast latest slots + bookings
    slots = get_slots_sync(db)
    bookings = get_bookings_sync(db)
    trigger_broadcast(slots, bookings)

    return {"status": "cancelled", "booking_id": booking_id}

# Mark booking as paid
@router.post("/{booking_id}/paid")
async def mark_booking_paid(booking_id: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = "paid"
    db.commit()

    # 👇 broadcast latest slots + bookings
    slots = get_slots_sync(db)
    bookings = get_bookings_sync(db)
    trigger_broadcast(slots, bookings)

    return {"status": "paid", "booking_id": booking_id}
