from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter(prefix="/slots", tags=["Slots"])

# ✅ Get all slots
@router.get("/")
def get_slots(db: Session = Depends(database.get_db)):
    return db.query(models.Slot).all()


# ✅ Create a new slot
@router.post("/")
def create_slot(slot: schemas.SlotCreate, db: Session = Depends(database.get_db)):
    db_slot = models.Slot(**slot.dict())
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot


# ✅ Delete a slot
@router.delete("/{slot_id}")
def delete_slot(slot_id: int, db: Session = Depends(database.get_db)):
    slot = db.query(models.Slot).filter(models.Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    db.delete(slot)
    db.commit()
    return {"ok": True, "deleted_id": slot_id}
