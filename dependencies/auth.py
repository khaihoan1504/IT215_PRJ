from typing import List
import jwt
from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.config import settings
from core.exceptions import CustomException
from db.database import get_db
from models.user import User
security = HTTPBearer()
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    credentials_exception = CustomException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Xác thực thất bại"
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "access":
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise CustomException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token đã hết hạn"
        )
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản đã bị khóa"
        )
    return current_user
class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise CustomException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Không đủ quyền truy cập (Yêu cầu: {', '.join(self.allowed_roles)})",
            )
        return current_user
get_admin_user = RoleChecker(["ADMIN"])
