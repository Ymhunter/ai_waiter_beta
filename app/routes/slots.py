from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import Slot, to_date, to_time, get_db
from ..helpers import get_slots_sync, get_bookings_sync
from ..websocket_manager import trigger_broadcast

router = APIRouter(prefix="/api/slots", tags=["slots"])


# ------------------------------
# Get all available slots
# ------------------------------
@router.get("")
async def get_slots(db: Session = Depends(get_db)):
    return get_slots_sync(db)


# ------------------------------
# Add a new slot
# ------------------------------
@router.post("")
async def add_slot(slot: dict = Body(...), db: Session = Depends(get_db)):
    d = to_date(slot.get("date"))
    t = to_time(slot.get("time"))
    if not d or not t:
        raise HTTPException(status_code=400, detail=f"Invalid date/time: {slot}")

    if t.strftime("%H:%M") == "00:00":
        raise HTTPException(status_code=400, detail="Please select a valid time")

    existing = db.query(Slot).filter_by(date=d, time=t).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slot already exists")

    new_slot = Slot(date=d, time=t, available=True)
    db.add(new_slot)
    db.commit()

    slots = get_slots_sync(db)
    bookings = get_bookings_sync(db)
    trigger_broadcast(slots, bookings)

    return {"status": "ok"}


# ------------------------------
# Delete a slot
# ------------------------------
@router.delete("")
async def delete_slot(date: str, time: str, db: Session = Depends(get_db)):
    d = to_date(date)
    t = to_time(time)
    if not d or not t:
        raise HTTPException(
            status_code=400, detail=f"Invalid date/time: {date} {time}"
        )

    slot = db.query(Slot).filter_by(date=d, time=t).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    db.delete(slot)
    db.commit()

    slots = get_slots_sync(db)
    bookings = get_bookings_sync(db)
    trigger_broadcast(slots, bookings)

    return {"status": "deleted"}
