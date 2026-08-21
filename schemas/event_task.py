from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class EventTaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "PENDING"

class EventTaskCreate(EventTaskBase):
    event_id: int
    assignee_id: Optional[int] = None

class EventTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assignee_id: Optional[int] = None

class EventTaskResponse(EventTaskBase):
    id: int
    event_id: int
    assignee_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
