import os
import uuid
from typing import Tuple
from fastapi import UploadFile
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "docx"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 5 * 1024 * 1024        
async def save_upload_file(file: UploadFile) -> Tuple[bool, str]:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return False, f"Định dạng MIME không hợp lệ: {file.content_type}"
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Phần mở rộng file không được hỗ trợ: .{ext}"
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        return False, f"Dung lượng file vượt quá giới hạn cho phép ({MAX_FILE_SIZE // (1024*1024)}MB)"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(contents)
    return True, f"/{UPLOAD_DIR}/{unique_filename}"
