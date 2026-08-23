from pydantic import BaseModel, ConfigDict
from typing import Optional
class EventStaffCreate(BaseModel):
    user_id: int
    role: str = "MEMBER" 
class EventStaffResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    role: str
    model_config = ConfigDict(from_attributes=True)
