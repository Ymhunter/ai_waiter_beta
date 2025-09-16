from pydantic import BaseModel
from datetime import datetime

class SlotBase(BaseModel):
    start_time: datetime
    end_time: datetime

class SlotCreate(SlotBase):
    pass

class SlotResponse(SlotBase):
    id: int
    available: bool
    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    slot_id: int
    customer_name: str
    customer_email: str

class BookingResponse(BaseModel):
    id: int
    slot_id: int
    status: str
    class Config:
        from_attributes = True
