import os
from datetime import datetime, date as DateType, time as TimeType
from sqlalchemy import (
    create_engine, Column, String, Integer, Boolean,
    inspect, text, Date, Time, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ------------------------------
# Database URL
# ------------------------------
# Example MySQL URL: mysql+pymysql://user:password@host:3306/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # ✅ fallback to SQLite if no MySQL configured
    DATABASE_URL = "sqlite:///./barbershop.db"

# ------------------------------
# Create SQLAlchemy Engine
# ------------------------------
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ------------------------------
# Models
# ------------------------------
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    service = Column(String)
    date = Column(Date)
    time = Column(Time)
    status = Column(String, default="pending")
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())


class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, index=True)
    time = Column(Time)
    available = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("date", "time", name="uq_slot_datetime"),)


# ------------------------------
# Create tables
# ------------------------------
Base.metadata.create_all(bind=engine)

# ------------------------------
# Helpers
# ------------------------------
def to_date(v):
    if not v:
        return None
    if isinstance(v, DateType):
        return v
    try:
        return datetime.fromisoformat(str(v)).date()
    except Exception:
        try:
            return datetime.strptime(str(v), "%Y-%m-%d").date()
        except Exception:
            return None


def to_time(v):
    if not v:
        return None
    if isinstance(v, TimeType):
        return v
    text_v = str(v)
    try:
        if "Z" in text_v:
            text_v = text_v.replace("Z", "")
        return datetime.fromisoformat(f"2000-01-01T{text_v}").time()
    except Exception:
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(text_v, fmt).time()
            except Exception:
                continue
    return None
