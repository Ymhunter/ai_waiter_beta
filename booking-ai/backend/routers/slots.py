from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter(prefix="/slots", tags=["Slots"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.SlotResponse)
def create_slot(slot: schemas.SlotCreate, db: Session = Depends(get_db)):
    new_slot = models.Slot(start_time=slot.start_time, end_time=slot.end_time)
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    return new_slot

@router.get("/", response_model=list[schemas.SlotResponse])
def get_slots(db: Session = Depends(get_db)):
    return db.query(models.Slot).filter(models.Slot.available == True).all()
