from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Kiểm tra trạng thái server", description="Trả về trạng thái hoạt động hiện tại của hệ thống.")
def health_check():
    return {"status": "ok", "message": "API is healthy"}

