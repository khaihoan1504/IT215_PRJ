from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.exceptions import CustomException
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.schemas.event_staff import EventStaffCreate, EventStaffResponse
from app.schemas.activity_log import ActivityLogResponse
from app.services import event_service, activity_log_service

router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo sự kiện mới",
    description="Tạo sự kiện mới và tự động gán người tạo là OWNER trong ban tổ chức.",
)
def create_event(
    event_in: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return event_service.create_event(db, event_in, creator_id=current_user.id)


@router.get(
    "",
    response_model=List[EventResponse],
    summary="Danh sách sự kiện",
    description="Lấy danh sách sự kiện mà người dùng hiện tại đang tham gia (lọc sự kiện đã xóa mềm). "
                "Hỗ trợ tìm kiếm theo tên và phân trang limit/offset.",
)
def get_events(
    search: Optional[str] = Query(None, description="Tìm theo tên sự kiện"),
    skip: int = Query(0, ge=0, description="Số lượng bản ghi bỏ qua (offset)"),
    limit: int = Query(20, ge=1, le=100, description="Số lượng bản ghi tối đa (limit)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return event_service.get_user_events(
        db=db, user_id=current_user.id, search=search, skip=skip, limit=limit
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Chi tiết sự kiện",
    description="Lấy thông tin chi tiết một sự kiện. Chỉ thành viên của sự kiện mới được xem.",
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    event = event_service.get_event_by_id(db, event_id)
    if not event:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sự kiện không tồn tại"
        )
    staff = event_service.get_event_staff(db, event_id=event_id, user_id=current_user.id)
    if not staff:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem sự kiện này",
        )
    return event


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    summary="Cập nhật sự kiện",
    description="Cập nhật thông tin sự kiện. Chỉ OWNER của sự kiện mới có quyền cập nhật.",
)
def update_event(
    event_id: int,
    event_in: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    event = event_service.get_event_by_id(db, event_id)
    if not event:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sự kiện không tồn tại"
        )
    staff = event_service.get_event_staff(db, event_id=event_id, user_id=current_user.id)
    if not staff or staff.role != "OWNER":
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER mới có quyền cập nhật sự kiện",
        )
    return event_service.update_event(db, event, event_in, user_id=current_user.id)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa mềm sự kiện",
    description="Xóa mềm sự kiện (soft delete) — đánh dấu is_deleted=True, không mất dữ liệu. "
                "Chỉ OWNER của sự kiện mới có quyền xóa.",
)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    event = event_service.get_event_by_id(db, event_id)
    if not event:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sự kiện không tồn tại"
        )
    staff = event_service.get_event_staff(db, event_id=event_id, user_id=current_user.id)
    if not staff or staff.role != "OWNER":
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER mới có quyền xóa sự kiện",
        )
    event_service.delete_event(db, event, user_id=current_user.id)
    return {"detail": "Đã xóa sự kiện thành công (soft delete)"}


@router.post(
    "/{event_id}/members",
    response_model=EventStaffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm thành viên vào sự kiện",
    description="Thêm thành viên mới vào ban tổ chức sự kiện. Chỉ OWNER mới có quyền thêm.",
)
def add_member(
    event_id: int,
    staff_in: EventStaffCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    event = event_service.get_event_by_id(db, event_id)
    if not event:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sự kiện không tồn tại"
        )
    current_staff = event_service.get_event_staff(db, event_id=event_id, user_id=current_user.id)
    if not current_staff or current_staff.role != "OWNER":
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER mới được thêm thành viên",
        )
    new_staff, error_msg, sc = event_service.add_event_member(
        db, event_id=event_id, staff_in=staff_in, user_id=current_user.id
    )
    if error_msg:
        raise CustomException(status_code=sc, detail=error_msg)
    return new_staff


@router.get(
    "/{event_id}/members",
    response_model=List[EventStaffResponse],
    summary="Danh sách thành viên sự kiện",
    description="Lấy danh sách thành viên ban tổ chức của sự kiện. "
                "Chỉ thành viên sự kiện mới được xem.",
)
def get_members(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    staff = event_service.get_event_staff(db, event_id=event_id, user_id=current_user.id)
    if not staff:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem danh sách thành viên",
        )
    return event_service.get_event_members(db, event_id=event_id)


@router.delete(
    "/{event_id}/members/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa thành viên khỏi sự kiện",
    description="Xóa thành viên khỏi ban tổ chức sự kiện. Chỉ OWNER mới có quyền xóa. "
                "Không thể xóa OWNER duy nhất.",
)
def remove_member(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    current_staff = event_service.get_event_staff(db, event_id=event_id, user_id=current_user.id)
    if not current_staff or current_staff.role != "OWNER":
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER mới được xóa thành viên",
        )
    success, error_msg, sc = event_service.remove_event_member(
        db, event_id=event_id, user_id=user_id, actor_id=current_user.id
    )
    if not success:
        raise CustomException(status_code=sc, detail=error_msg)
    return {"detail": "Đã xóa thành viên thành công"}


@router.get(
    "/{event_id}/activity-logs",
    response_model=List[ActivityLogResponse],
    summary="Lịch sử hoạt động sự kiện",
    description="Lấy danh sách lịch sử các thao tác quan trọng trên sự kiện "
                "(tạo/sửa/xóa sự kiện, thêm/xóa thành viên). Chỉ thành viên mới được xem.",
)
def get_activity_logs(
    event_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    staff = event_service.get_event_staff(db, event_id=event_id, user_id=current_user.id)
    if not staff:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem lịch sử hoạt động",
        )
    return activity_log_service.get_event_activity_logs(
        db, event_id=event_id, skip=skip, limit=limit
    )

