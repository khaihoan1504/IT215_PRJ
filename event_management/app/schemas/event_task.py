from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class EventTaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề công việc")
    description: Optional[str] = Field(None, description="Mô tả chi tiết công việc")


class EventTaskCreate(EventTaskBase):
    assignee_id: Optional[int] = Field(None, description="ID nhân sự được giao (phải là thành viên sự kiện)")
    status: TaskStatus = Field(TaskStatus.TODO, description="Trạng thái: TODO, IN_PROGRESS, DONE")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Mức ưu tiên: LOW, MEDIUM, HIGH")
    due_date: Optional[datetime] = Field(None, description="Hạn hoàn thành")


class EventTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Tiêu đề công việc")
    description: Optional[str] = Field(None, description="Mô tả chi tiết công việc")
    status: Optional[TaskStatus] = Field(None, description="Trạng thái: TODO, IN_PROGRESS, DONE")
    priority: Optional[TaskPriority] = Field(None, description="Mức ưu tiên: LOW, MEDIUM, HIGH")
    assignee_id: Optional[int] = Field(None, description="ID nhân sự được giao (phải là thành viên sự kiện)")
    due_date: Optional[datetime] = Field(None, description="Hạn hoàn thành")


class EventTaskResponse(BaseModel):
    id: int
    event_id: int
    assignee_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

