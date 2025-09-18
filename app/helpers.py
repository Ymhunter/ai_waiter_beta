from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import Slot, Booking, to_date, to_time

def clean_expired_slots(db: Session):
    now = datetime.now()
    for s in db.query(Slot).all():
        try:
            slot_dt = datetime.combine(to_date(s.date), to_time(s.time))
            if slot_dt <= now:
                db.delete(s)
        except Exception:
            continue
    db.commit()

def clean_stale_bookings(db: Session):
    now = datetime.utcnow()
    stale = db.query(Booking).filter_by(status="pending").all()
    for b in stale:
        try:
            created = datetime.fromisoformat(b.created_at)
        except Exception:
            created = now - timedelta(hours=1)
        if created + timedelta(minutes=10) < now:
            slot = db.query(Slot).filter_by(date=b.date, time=b.time).first()
            if slot:
                slot.available = True
            db.delete(b)
    db.commit()

def get_slots_sync(db: Session):
    clean_expired_slots(db)
    clean_stale_bookings(db)
    slots = db.query(Slot).filter_by(available=True).all()
    result: dict[str, list[str]] = {}
    for s in slots:
        d = to_date(s.date)
        t = to_time(s.time)
        if not d or not t:
            continue
        result.setdefault(d.isoformat(), []).append(t.strftime("%H:%M"))
    for d, times in result.items():
        result[d] = sorted(set(times))
    return result

def get_bookings_sync(db: Session):
    clean_stale_bookings(db)
    bookings = db.query(Booking).all()
    result = []
    for b in bookings:
        result.append({
            "id": b.id,
            "customer_name": b.customer_name,
            "service": b.service,
            "date": b.date.isoformat() if b.date else None,
            "time": b.time.strftime("%H:%M") if b.time else None,
            "status": b.status
        })
    return result
