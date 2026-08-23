import os
import uuid
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile
from models.task_attachment import TaskAttachment
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "docx", "doc", "xlsx", "pptx", "txt"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
}
MAX_FILE_SIZE = 10 * 1024 * 1024         
async def save_task_attachment(
    db: Session, task_id: int, uploader_id: int, file: UploadFile
) -> Tuple[Optional[TaskAttachment], Optional[str], int]:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return None, f"Loại file không được hỗ trợ: {file.content_type}", 400
    original_filename = file.filename or "unknown"
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return None, f"Phần mở rộng file không hợp lệ: .{ext}", 400
    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE:
        return None, f"Dung lượng file vượt quá giới hạn ({MAX_FILE_SIZE // (1024*1024)}MB)", 400
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)
    with open(file_path, "wb") as f:
        f.write(contents)
    attachment = TaskAttachment(
        task_id=task_id,
        uploader_id=uploader_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_url=f"/uploads/{stored_filename}",
        content_type=file.content_type,
        file_size=file_size,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment, None, 201
def get_attachments_by_task(db: Session, task_id: int) -> List[TaskAttachment]:
    return (
        db.query(TaskAttachment)
        .filter(TaskAttachment.task_id == task_id)
        .order_by(TaskAttachment.created_at.desc())
        .all()
    )
def get_attachment_by_id(db: Session, attachment_id: int) -> Optional[TaskAttachment]:
    return db.query(TaskAttachment).filter(TaskAttachment.id == attachment_id).first()
def delete_attachment(db: Session, attachment: TaskAttachment) -> None:
    file_path = os.path.join(UPLOAD_DIR, attachment.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(attachment)
    db.commit()
