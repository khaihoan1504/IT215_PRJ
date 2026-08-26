from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class EventTask(Base):
    __tablename__ = "event_tasks"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(50),
        default="TODO",
        nullable=False,
        comment="Trạng thái: TODO, IN_PROGRESS, DONE",
    )
    priority = Column(
        String(50),
        default="MEDIUM",
        nullable=False,
        comment="Mức ưu tiên: LOW, MEDIUM, HIGH",
    )
    due_date = Column(DateTime(timezone=True), nullable=True, comment="Hạn hoàn thành")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    event = relationship("Event", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")


