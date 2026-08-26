from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)


def register_user(db: Session, user_in: UserCreate) -> Tuple[Optional[User], Optional[str]]:
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        return None, "Email đã được sử dụng"

    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role="USER",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user, None


def authenticate_user(db: Session, user_in: UserLogin) -> Tuple[Optional[dict], Optional[str], int]:
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        return None, "Sai email hoặc mật khẩu", 401

    if not user.is_active:
        return None, "Tài khoản đã bị khóa", 400

    token_data = {
        "access_token": create_access_token(data={"sub": user.email}),
        "refresh_token": create_refresh_token(data={"sub": user.email}),
        "token_type": "bearer",
    }
    return token_data, None, 200


def refresh_access_token(db: Session, refresh_token: str) -> Tuple[Optional[dict], Optional[str], int]:
    email = decode_refresh_token(refresh_token)
    if email is None:
        return None, "Refresh token không hợp lệ hoặc đã hết hạn", 401

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None, "Người dùng không tồn tại", 401

    if not user.is_active:
        return None, "Tài khoản đã bị khóa", 400

    token_data = {
        "access_token": create_access_token(data={"sub": user.email}),
        "refresh_token": create_refresh_token(data={"sub": user.email}),
        "token_type": "bearer",
    }
    return token_data, None, 200

