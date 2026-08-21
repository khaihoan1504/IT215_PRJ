from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from db.database import get_db
from dependencies.auth import get_current_active_user, get_admin_user
from models.user import User
from schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("", response_model=List[UserResponse])
def get_users(
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc email"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    query = db.query(User)
    
    if search:
        query = query.filter((User.email.ilike(f"%{search}%")) | (User.full_name.ilike(f"%{search}%")))
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
        
    return query.all()