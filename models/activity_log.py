from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="Người thực hiện")
    action = Column(String(100), nullable=False, comment="Loại hành động: CREATE_EVENT, UPDATE_EVENT, DELETE_EVENT, ADD_MEMBER, REMOVE_MEMBER, ...")
    target_type = Column(String(100), nullable=False, comment="Đối tượng: EVENT, EVENT_STAFF, EVENT_TASK")
    target_id = Column(Integer, nullable=True, comment="ID của đối tượng bị tác động")
    detail = Column(Text, nullable=True, comment="Mô tả chi tiết hành động")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="activity_logs")
