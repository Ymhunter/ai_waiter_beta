from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..deps import get_db
from ..helpers import get_slots_sync
from ..database import Slot, to_date, to_time
from ..websocket_manager import trigger_broadcast

router = APIRouter()

@router.get("/api/slots")
async def get_slots(db: Session = Depends(get_db)):
    return JSONResponse(get_slots_sync(db), headers={"Cache-Control": "no-store"})

@router.post("/api/slots")
async def add_slot(slot: dict = Body(...), db: Session = Depends(get_db)):
    d = to_date(slot.get("date"))
    t = to_time(slot.get("time"))
    if not d or not t:
        raise HTTPException(status_code=400, detail=f"Invalid date/time: {slot}")

    existing = db.query(Slot).filter_by(date=d, time=t).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slot already exists")

    try:
        new_slot = Slot(date=d, time=t, available=True)
        db.add(new_slot)
        db.commit()
        trigger_broadcast(db)
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/api/slots")
async def delete_slot(date: str, time: str, db: Session = Depends(get_db)):
    d = to_date(date)
    t = to_time(time)
    if not d or not t:
        raise HTTPException(status_code=400, detail=f"Invalid date/time: {date} {time}")
    slot = db.query(Slot).filter_by(date=d, time=t).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    try:
        db.delete(slot)
        db.commit()
        trigger_broadcast(db)
        return {"status": "deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
