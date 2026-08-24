from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from db.database import get_db
from schemas.user import (
    UserCreate,
    UserResponse,
    Token,
    UserLogin,
    RefreshTokenRequest,
)
from core.exceptions import CustomException
from services import auth_service

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản",
    description="Đăng ký tài khoản người dùng mới bằng email, mật khẩu và họ tên. "
                "Trả về 400 nếu email đã tồn tại.",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    new_user, error_msg = auth_service.register_user(db, user_in)
    if error_msg:
        raise CustomException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="Đăng nhập",
    description="Đăng nhập bằng email và mật khẩu. Trả về JWT access token và refresh token (Bearer). "
                "Giới hạn tối đa 5 lần/phút để chống brute-force. "
                "Trả về 401 nếu sai thông tin, 400 nếu tài khoản bị khóa.",
)
@limiter.limit("5/minute")
def login(request: Request, user_in: UserLogin, db: Session = Depends(get_db)):
    token_data, error_msg, status_code = auth_service.authenticate_user(db, user_in)
    if error_msg:
        raise CustomException(status_code=status_code, detail=error_msg)
    return token_data


@router.post(
    "/refresh",
    response_model=Token,
    summary="Cấp lại access token",
    description="Sử dụng refresh token hợp lệ để cấp lại cặp access token + refresh token mới. "
                "Refresh token có thời hạn 7 ngày. Trả về 401 nếu token không hợp lệ hoặc hết hạn.",
)
def refresh_token(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    token_data, error_msg, status_code = auth_service.refresh_access_token(db, body.refresh_token)
    if error_msg:
        raise CustomException(status_code=status_code, detail=error_msg)
    return token_data

