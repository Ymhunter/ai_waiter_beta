from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..deps import get_db
from ..helpers import get_bookings_sync
from ..database import Booking, Slot
from ..websocket_manager import trigger_broadcast

router = APIRouter()

@router.get("/api/bookings")
async def get_bookings(db: Session = Depends(get_db)):
    return JSONResponse(get_bookings_sync(db), headers={"Cache-Control": "no-store"})

@router.post("/api/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = "cancelled"
    slot = db.query(Slot).filter_by(date=booking.date, time=booking.time).first()
    if slot:
        slot.available = True
    db.commit()
    trigger_broadcast(db)
    return {"status": "cancelled", "booking_id": booking_id}

@router.post("/api/bookings/{booking_id}/paid")
async def mark_booking_paid(booking_id: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter_by(id=booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = "paid"
    db.commit()
    trigger_broadcast(db)
    return {"status": "paid", "booking_id": booking_id}
