from fastapi import APIRouter, Depends, UploadFile, File, status

from core.exceptions import CustomException
from dependencies.auth import get_current_active_user
from models.user import User
from schemas.upload import FileUploadResponse
from services.upload_service import save_upload_file

router = APIRouter(prefix="/upload", tags=["Uploads"])


@router.post(
    "",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên tệp tin",
    description="Tải lên tệp tin an toàn. Kiểm tra định dạng MIME type, phần mở rộng file "
                "và giới hạn dung lượng (5MB). File được lưu với tên UUID4 để tránh ghi đè.",
)
async def upload_file(
    file: UploadFile = File(..., description="Tệp tin cần tải lên"),
    current_user: User = Depends(get_current_active_user),
):
    success, result = await save_upload_file(file)
    if not success:
        raise CustomException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)
    return FileUploadResponse(
        filename=file.filename or "unknown",
        url=result,
        message="Tải lên tệp tin thành công",
    )

