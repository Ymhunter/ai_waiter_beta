from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class Worker(Base):
    __tablename__ = "workers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    slots = relationship("Slot", back_populates="worker")

class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    available = Column(Boolean, default=True)

    worker = relationship("Worker", back_populates="slots")
    booking = relationship("Booking", back_populates="slot", uselist=False)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"))
    customer_name = Column(String)
    customer_email = Column(String)
    status = Column(String, default="confirmed")

    slot = relationship("Slot", back_populates="booking")


