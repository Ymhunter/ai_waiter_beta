import logging
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import Slot, to_date, to_time, get_db
from ..helpers import get_slots_sync, get_bookings_sync
from ..websocket_manager import trigger_broadcast

# Logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/slots", tags=["slots"])


# ------------------------------
# Get all available slots
# ------------------------------
@router.get("/")
async def get_slots(db: Session = Depends(get_db)):
    try:
        slots = get_slots_sync(db)
        logger.info(f"Fetched {sum(len(v) for v in slots.values())} slots")
        return slots
    except Exception as e:
        logger.error(f"Error fetching slots: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch slots")


# ------------------------------
# Add a new slot
# ------------------------------
@router.post("/")
async def add_slot(slot: dict = Body(...), db: Session = Depends(get_db)):
    logger.info(f"🟢 Received add_slot request: {slot}")

    d = to_date(slot.get("date"))
    t = to_time(slot.get("time"))

    if not d or not t:
        raise HTTPException(status_code=400, detail=f"Invalid date/time: {slot}")

    if t.strftime("%H:%M") == "00:00":
        raise HTTPException(status_code=400, detail="Please select a valid time")

    try:
        existing = db.query(Slot).filter_by(date=d, time=t).first()
        if existing:
            raise HTTPException(status_code=400, detail="Slot already exists")

        new_slot = Slot(date=d, time=t, available=True)
        db.add(new_slot)
        db.commit()

        # Broadcast updated state
        slots = get_slots_sync(db)
        bookings = get_bookings_sync(db)
        trigger_broadcast(slots, bookings)

        logger.info(f"✅ Slot added successfully: {d} {t}")
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error adding slot: {e}")
        raise HTTPException(status_code=500, detail="Database error")


# ------------------------------
# Delete a slot
# ------------------------------
@router.delete("/")
async def delete_slot(date: str, time: str, db: Session = Depends(get_db)):
    logger.info(f"🟠 Received delete_slot request: {date} {time}")

    d = to_date(date)
    t = to_time(time)
    if not d or not t:
        raise HTTPException(
            status_code=400, detail=f"Invalid date/time: {date} {time}"
        )

    try:
        slot = db.query(Slot).filter_by(date=d, time=t).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")

        db.delete(slot)
        db.commit()

        # Broadcast updated state
        slots = get_slots_sync(db)
        bookings = get_bookings_sync(db)
        trigger_broadcast(slots, bookings)

        logger.info(f"✅ Slot deleted successfully: {d} {t}")
        return {"status": "deleted"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error deleting slot: {e}")
        raise HTTPException(status_code=500, detail="Database error")
