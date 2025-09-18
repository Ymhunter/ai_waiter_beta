from pydantic import BaseModel


# -------------------------------
# Slot Schemas
# -------------------------------
class SlotBase(BaseModel):
    date: str
    time: str


class SlotCreate(SlotBase):
    pass


class Slot(SlotBase):
    id: int

    class Config:
        orm_mode = True


# -------------------------------
# Booking Schemas
# -------------------------------
class BookingBase(BaseModel):
    customer_name: str
    customer_email: str
    slot_id: int


class BookingCreate(BookingBase):
    pass


class Booking(BookingBase):
    id: int
    slot: Slot  # nested slot data

    class Config:
        orm_mode = True
