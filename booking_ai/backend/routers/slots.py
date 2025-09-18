from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter(prefix="/slots", tags=["Slots"])


@@router.get("/")
def get_slots(db: Session = Depends(database.get_db)):
    slots = db.query(models.Slot).all()
    return [{"id": s.id, "time": s.time} for s in slots]


@router.post("/")
def create_slot(slot: schemas.SlotCreate, db: Session = Depends(database.get_db)):
    # ✅ For Pydantic v2
    db_slot = models.Slot(**slot.model_dump())
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot


@router.delete("/{slot_id}")
def delete_slot(slot_id: int, db: Session = Depends(database.get_db)):
    # ✅ For SQLAlchemy 2.x
    slot = db.get(models.Slot, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    db.delete(slot)
    db.commit()
    return {"ok": True}
