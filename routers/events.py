from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db.database import get_db
from core.exceptions import CustomException
from dependencies.auth import get_current_active_user
from models.user import User
from models.event import Event
from models.event_staff import EventStaff
from schemas.event import EventCreate, EventResponse, EventUpdate
from schemas.event_staff import EventStaffCreate, EventStaffResponse

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event_in: EventCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    new_event = Event(**event_in.model_dump(), creator_id=current_user.id)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    owner_staff = EventStaff(event_id=new_event.id, user_id=current_user.id, role="OWNER")
    db.add(owner_staff)
    db.commit()

    return new_event

@router.get("", response_model=List[EventResponse])
def get_events(
    search: Optional[str] = Query(None, description="Tìm theo tên sự kiện"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    
    query = db.query(Event).join(EventStaff).filter(EventStaff.user_id == current_user.id)
    
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
        
    return query.all()

@router.get("/{id}", response_model=EventResponse)
def get_event(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    event = db.query(Event).filter(Event.id == id).first()
    if not event:
        raise CustomException(status_code=404, detail="Sự kiện không tồn tại")

    is_member = db.query(EventStaff).filter(EventStaff.event_id == id, EventStaff.user_id == current_user.id).first()
    if not is_member:
        raise CustomException(status_code=403, detail="Bạn không có quyền xem sự kiện này")

    return event

@router.put("/{id}", response_model=EventResponse)
def update_event(id: int, event_in: EventUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    event = db.query(Event).filter(Event.id == id).first()
    if not event:
        raise CustomException(status_code=404, detail="Sự kiện không tồn tại")
    
    staff = db.query(EventStaff).filter(EventStaff.event_id == id, EventStaff.user_id == current_user.id).first()
    if not staff or staff.role != "OWNER":
        raise CustomException(status_code=403, detail="Chỉ OWNER mới có quyền cập nhật sự kiện")

    update_data = event_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return event

@router.delete("/{id}")
def delete_event(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    event = db.query(Event).filter(Event.id == id).first()
    if not event:
        raise CustomException(status_code=404, detail="Sự kiện không tồn tại")

    staff = db.query(EventStaff).filter(EventStaff.event_id == id, EventStaff.user_id == current_user.id).first()
    if not staff or staff.role != "OWNER":
        raise CustomException(status_code=403, detail="Chỉ OWNER mới có quyền xóa sự kiện")

    db.query(EventStaff).filter(EventStaff.event_id == id).delete()
    db.delete(event)
    db.commit()
    return {"detail": "Đã xóa sự kiện thành công"}

@router.post("/{id}/members", response_model=EventStaffResponse)
def add_member(id: int, staff_in: EventStaffCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    event = db.query(Event).filter(Event.id == id).first()
    if not event:
        raise CustomException(status_code=404, detail="Sự kiện không tồn tại")

    current_staff = db.query(EventStaff).filter(EventStaff.event_id == id, EventStaff.user_id == current_user.id).first()
    if not current_staff or current_staff.role != "OWNER":
        raise CustomException(status_code=403, detail="Chỉ OWNER mới được thêm thành viên")

    target_user = db.query(User).filter(User.id == staff_in.user_id).first()
    if not target_user:
        raise CustomException(status_code=404, detail="Người dùng này không tồn tại trên hệ thống")

    existing_member = db.query(EventStaff).filter(EventStaff.event_id == id, EventStaff.user_id == staff_in.user_id).first()
    if existing_member:
        raise CustomException(status_code=400, detail="Người dùng này đã là thành viên của sự kiện")

    new_staff = EventStaff(event_id=id, user_id=staff_in.user_id, role=staff_in.role)
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)
    return new_staff

@router.get("/{id}/members", response_model=List[EventStaffResponse])
def get_members(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    is_member = db.query(EventStaff).filter(EventStaff.event_id == id, EventStaff.user_id == current_user.id).first()
    if not is_member:
        raise CustomException(status_code=403, detail="Bạn không có quyền xem danh sách thành viên")

    members = db.query(EventStaff).filter(EventStaff.event_id == id).all()
    return members

@router.delete("/{id}/members/{user_id}")
def remove_member(id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    current_staff = db.query(EventStaff).filter(EventStaff.event_id == id, EventStaff.user_id == current_user.id).first()
    if not current_staff or current_staff.role != "OWNER":
        raise CustomException(status_code=403, detail="Chỉ OWNER mới được xóa thành viên")

    target_staff = db.query(EventStaff).filter(EventStaff.event_id == id, EventStaff.user_id == user_id).first()
    if not target_staff:
        raise CustomException(status_code=404, detail="Thành viên không tồn tại trong sự kiện này")

    if target_staff.role == "OWNER":
        owner_count = db.query(EventStaff).filter(EventStaff.event_id == id, EventStaff.role == "OWNER").count()
        if owner_count <= 1:
            raise CustomException(status_code=400, detail="Không thể xóa OWNER duy nhất của sự kiện. Vui lòng cấp quyền OWNER cho người khác trước.")

    db.delete(target_staff)
    db.commit()
    return {"detail": "Đã xóa thành viên thành công"}