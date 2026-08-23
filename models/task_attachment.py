from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
class TaskAttachment(Base):
    __tablename__ = "task_attachments"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("event_tasks.id", ondelete="CASCADE"), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(500), nullable=False, comment="Tên gốc file người dùng upload")
    stored_filename = Column(String(500), nullable=False, comment="Tên file lưu trữ trên server (uuid)")
    file_url = Column(String(1000), nullable=False, comment="Đường dẫn truy cập file")
    content_type = Column(String(255), nullable=True, comment="MIME type: image/png, application/pdf...")
    file_size = Column(BigInteger, nullable=True, comment="Kích thước file (bytes)")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    task = relationship("EventTask", back_populates="attachments")
    uploader = relationship("User", back_populates="attachments")
