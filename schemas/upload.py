from pydantic import BaseModel
class FileUploadResponse(BaseModel):
    filename: str
    url: str
    message: str = "Tải lên tệp thành công"
