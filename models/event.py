from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    creator_id = Column(Integer, ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False, nullable=False, comment="Soft delete flag")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="Thời điểm xóa mềm")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    creator = relationship("User", back_populates="events")
    staffs = relationship("EventStaff", back_populates="event")
    tasks = relationship("EventTask", back_populates="event")
