from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tên sự kiện không được để trống")
    description: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class EventResponse(EventBase):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

