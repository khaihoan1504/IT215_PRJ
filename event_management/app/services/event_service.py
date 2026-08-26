from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload

from app.models.event import Event
from app.models.event_staff import EventStaff
from app.models.user import User
from app.schemas.event import EventCreate, EventUpdate
from app.schemas.event_staff import EventStaffCreate
from app.services import activity_log_service


def create_event(db: Session, event_in: EventCreate, creator_id: int) -> Event:
    new_event = Event(**event_in.model_dump(), creator_id=creator_id)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    owner_staff = EventStaff(event_id=new_event.id, user_id=creator_id, role="OWNER")
    db.add(owner_staff)
    db.commit()

    activity_log_service.log_activity(
        db,
        user_id=creator_id,
        action="CREATE_EVENT",
        target_type="EVENT",
        target_id=new_event.id,
        detail=f"Tạo sự kiện '{new_event.title}'",
    )
    return new_event


def get_user_events(
    db: Session,
    user_id: int,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Event]:
    query = (
        db.query(Event)
        .options(joinedload(Event.creator))
        .join(EventStaff, EventStaff.event_id == Event.id)
        .filter(EventStaff.user_id == user_id)
        .filter(Event.is_deleted == False)
    )
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def get_event_by_id(db: Session, event_id: int) -> Optional[Event]:
    return (
        db.query(Event)
        .options(
            joinedload(Event.creator),
            joinedload(Event.staffs),
            joinedload(Event.tasks),
        )
        .filter(Event.id == event_id, Event.is_deleted == False)
        .first()
    )


def get_event_staff(db: Session, event_id: int, user_id: int) -> Optional[EventStaff]:
    return (
        db.query(EventStaff)
        .filter(EventStaff.event_id == event_id, EventStaff.user_id == user_id)
        .first()
    )


def update_event(db: Session, event: Event, event_in: EventUpdate, user_id: int = None) -> Event:
    update_data = event_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)

    if user_id:
        activity_log_service.log_activity(
            db,
            user_id=user_id,
            action="UPDATE_EVENT",
            target_type="EVENT",
            target_id=event.id,
            detail=f"Cập nhật sự kiện '{event.title}': {', '.join(update_data.keys())}",
        )
    return event


def delete_event(db: Session, event: Event, user_id: int = None) -> None:
    event.is_deleted = True
    event.deleted_at = datetime.now(timezone.utc)
    db.commit()

    if user_id:
        activity_log_service.log_activity(
            db,
            user_id=user_id,
            action="DELETE_EVENT",
            target_type="EVENT",
            target_id=event.id,
            detail=f"Xóa mềm sự kiện '{event.title}'",
        )


def add_event_member(
    db: Session, event_id: int, staff_in: EventStaffCreate, user_id: int = None
) -> Tuple[Optional[EventStaff], Optional[str], int]:
    target_user = db.query(User).filter(User.id == staff_in.user_id).first()
    if not target_user:
        return None, "Người dùng này không tồn tại trên hệ thống", 404

    existing_member = (
        db.query(EventStaff)
        .filter(
            EventStaff.event_id == event_id,
            EventStaff.user_id == staff_in.user_id,
        )
        .first()
    )
    if existing_member:
        return None, "Người dùng này đã là thành viên của sự kiện", 400

    new_staff = EventStaff(
        event_id=event_id,
        user_id=staff_in.user_id,
        role=staff_in.role,
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)

    if user_id:
        activity_log_service.log_activity(
            db,
            user_id=user_id,
            action="ADD_MEMBER",
            target_type="EVENT",
            target_id=event_id,
            detail=f"Thêm thành viên user_id={staff_in.user_id} với vai trò '{staff_in.role}'",
        )
    return new_staff, None, 201


def get_event_members(db: Session, event_id: int) -> List[EventStaff]:
    return (
        db.query(EventStaff)
        .options(joinedload(EventStaff.user))
        .filter(EventStaff.event_id == event_id)
        .all()
    )


def remove_event_member(
    db: Session, event_id: int, user_id: int, actor_id: int = None
) -> Tuple[bool, Optional[str], int]:
    target_staff = (
        db.query(EventStaff)
        .filter(
            EventStaff.event_id == event_id,
            EventStaff.user_id == user_id,
        )
        .first()
    )
    if not target_staff:
        return False, "Thành viên không tồn tại trong sự kiện này", 404

    if target_staff.role == "OWNER":
        owner_count = (
            db.query(EventStaff)
            .filter(EventStaff.event_id == event_id, EventStaff.role == "OWNER")
            .count()
        )
        if owner_count <= 1:
            return (
                False,
                "Không thể xóa OWNER duy nhất của sự kiện. Vui lòng cấp quyền OWNER cho người khác trước.",
                400,
            )

    db.delete(target_staff)
    db.commit()

    if actor_id:
        activity_log_service.log_activity(
            db,
            user_id=actor_id,
            action="REMOVE_MEMBER",
            target_type="EVENT",
            target_id=event_id,
            detail=f"Xóa thành viên user_id={user_id} khỏi sự kiện",
        )
    return True, None, 200

