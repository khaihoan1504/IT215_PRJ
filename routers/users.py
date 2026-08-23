from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from dependencies.auth import get_current_active_user, get_admin_user
from models.user import User
from schemas.user import UserResponse
from services import user_service
router = APIRouter(prefix="/users", tags=["Users"])
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Thông tin cá nhân",
    description="Lấy thông tin chi tiết của người dùng hiện tại đang đăng nhập (từ JWT token).",
)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
@router.get(
    "",
    response_model=List[UserResponse],
    summary="Danh sách người dùng",
    description="Lấy danh sách tất cả người dùng trên hệ thống (chỉ ADMIN). "
                "Hỗ trợ tìm kiếm theo tên/email, lọc theo trạng thái và phân trang limit/offset.",
)
def get_users(
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc email"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua (offset)"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng bản ghi tối đa (limit)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return user_service.get_users(
        db=db, search=search, is_active=is_active, skip=skip, limit=limit
    )
