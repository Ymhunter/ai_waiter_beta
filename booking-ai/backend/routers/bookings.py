from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter(prefix="/bookings", tags=["Bookings"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.BookingResponse)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    slot = db.query(models.Slot).filter(models.Slot.id == booking.slot_id, models.Slot.available == True).first()
    if not slot:
        return {"error": "Slot not available"}
    
    slot.available = False
    new_booking = models.Booking(
        slot_id=slot.id,
        customer_name=booking.customer_name,
        customer_email=booking.customer_email
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking
