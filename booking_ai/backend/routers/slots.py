from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, database

router = APIRouter(prefix="/slots", tags=["Slots"])


@router.get("/", response_model=list[schemas.Slot])
def get_slots(db: Session = Depends(database.get_db)):
    """Return all available slots"""
    return db.query(models.Slot).all()


@router.post("/", response_model=schemas.Slot)
def create_slot(slot: schemas.SlotCreate, db: Session = Depends(database.get_db)):
    """Create a new slot"""
    db_slot = models.Slot(**slot.dict())
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot


@router.delete("/{slot_id}")
def delete_slot(slot_id: int, db: Session = Depends(database.get_db)):
    """Delete a slot by ID"""
    slot = db.get(models.Slot, slot_id)  # ✅ modern SQLAlchemy way
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    db.delete(slot)
    db.commit()
    return {"ok": True}
