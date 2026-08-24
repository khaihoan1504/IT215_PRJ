from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Nội dung bình luận")


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Nội dung bình luận cập nhật")


class CommentResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

