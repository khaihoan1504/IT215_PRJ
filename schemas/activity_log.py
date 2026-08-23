from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    target_type: str
    target_id: Optional[int] = None
    detail: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
