from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class EventStaffBase(BaseModel):
    role: Optional[str] = None

class EventStaffCreate(EventStaffBase):
    event_id: int
    user_id: int

class EventStaffUpdate(EventStaffBase):
    pass

class EventStaffResponse(EventStaffBase):
    id: int
    event_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
