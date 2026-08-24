from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    id: int
    task_id: int
    uploader_id: int
    original_filename: str
    stored_filename: str
    file_url: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

