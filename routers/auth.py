from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from db.database import get_db
from models.user import User
from schemas.user import UserCreate, UserResponse, Token, UserLogin
from core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from core.exceptions import CustomException
from core.config import settings

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise CustomException(status_code=400, detail="Email đã được sử dụng")
    
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role="USER",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise CustomException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai email hoặc mật khẩu")
    
    if not user.is_active:
        raise CustomException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản đã bị khóa")

    return {
        "access_token": create_access_token(data={"sub": user.email}),
        "refresh_token": create_refresh_token(data={"sub": user.email}),
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if payload.get("type") != "refresh":
            raise CustomException(status_code=401, detail="Token không hợp lệ")
    except jwt.ExpiredSignatureError:
        raise CustomException(status_code=401, detail="Refresh token đã hết hạn, vui lòng login lại")
    except jwt.PyJWTError:
        raise CustomException(status_code=401, detail="Refresh token không hợp lệ")

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise CustomException(status_code=401, detail="User không tồn tại hoặc bị khóa")

    return {
        "access_token": create_access_token(data={"sub": user.email}),
        "refresh_token": create_refresh_token(data={"sub": user.email}),
        "token_type": "bearer"
    }