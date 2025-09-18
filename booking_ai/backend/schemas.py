from pydantic import BaseModel
from typing import Optional

# ------------------------
# Slots
# ------------------------
class SlotBase(BaseModel):
    date: str
    time: str

class SlotCreate(SlotBase):
    pass

class Slot(SlotBase):
    id: int

    class Config:
        from_attributes = True  # replaces orm_mode


# ------------------------
# Bookings
# ------------------------
class BookingBase(BaseModel):
    customer_name: str
    customer_email: str
    slot_id: int

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    slot: Optional[Slot] = None  # include slot info when joined

    class Config:
        from_attributes = True  # replaces orm_mode


# ------------------------
# Booking response
# ------------------------
class BookingResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    slot: Slot   # embed slot in response

    class Config:
        from_attributes = True
