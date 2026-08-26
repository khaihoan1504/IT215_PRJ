from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.exceptions import CustomException
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.event_task import EventTaskCreate, EventTaskUpdate, EventTaskResponse
from app.schemas.comment import CommentCreate, CommentResponse
from app.services import event_task_service, event_service, comment_service

router = APIRouter(tags=["Event Tasks"])



def _check_event_membership(db: Session, event_id: int, user_id: int):
    staff = event_service.get_event_staff(db, event_id=event_id, user_id=user_id)
    if not staff:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không phải thành viên của sự kiện này",
        )
    return staff


def _check_event_owner(db: Session, event_id: int, user_id: int):
    staff = _check_event_membership(db, event_id, user_id)
    if staff.role != "OWNER":
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ OWNER của sự kiện mới có quyền thực hiện thao tác này",
        )
    return staff


def _check_task_permission_for_update(db: Session, event_id: int, user_id: int, task):
    staff = _check_event_membership(db, event_id, user_id)
    if staff.role == "OWNER":
        return staff
    if task.assignee_id != user_id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn chỉ có thể cập nhật công việc được giao cho mình",
        )
    return staff


@router.post(
    "/events/{event_id}/event-tasks",
    response_model=EventTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo công việc mới cho sự kiện",
    description="Tạo công việc mới trong sự kiện. Chỉ OWNER hoặc MEMBER mới được tạo. "
                "Nếu gán assignee, người đó phải là thành viên của sự kiện.",
)
def create_task(
    event_id: int,
    task_in: EventTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    event = event_service.get_event_by_id(db, event_id)
    if not event:
        raise CustomException(status_code=status.HTTP_404_NOT_FOUND, detail="Sự kiện không tồn tại")
    _check_event_membership(db, event_id, current_user.id)
    new_task, error_msg, sc = event_task_service.create_task(db, event_id, task_in)
    if error_msg:
        raise CustomException(status_code=sc, detail=error_msg)
    return new_task


@router.get(
    "/events/{event_id}/event-tasks",
    response_model=List[EventTaskResponse],
    summary="Danh sách công việc của sự kiện",
    description="Trả về danh sách công việc thuộc sự kiện, không lộ công việc sự kiện khác. "
                "Hỗ trợ filter theo status, priority, assignee; search theo title; "
                "sort theo created_at/due_date; phân trang limit/offset.",
)
def list_tasks(
    event_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái: TODO, IN_PROGRESS, DONE"),
    priority: Optional[str] = Query(None, description="Lọc theo mức ưu tiên: LOW, MEDIUM, HIGH"),
    assignee_id: Optional[int] = Query(None, description="Lọc theo ID người được giao"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo tiêu đề công việc"),
    sort_by: str = Query("created_at", description="Trường sắp xếp: created_at, due_date, priority, status, title"),
    sort_order: str = Query("desc", description="Thứ tự sắp xếp: asc hoặc desc"),
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua (offset)"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi tối đa (limit)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    event = event_service.get_event_by_id(db, event_id)
    if not event:
        raise CustomException(status_code=404, detail="Sự kiện không tồn tại")
    _check_event_membership(db, event_id, current_user.id)
    return event_task_service.get_tasks_by_event(
        db,
        event_id,
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/event-tasks/{task_id}",
    response_model=EventTaskResponse,
    summary="Chi tiết công việc sự kiện",
    description="Lấy chi tiết công việc. Kiểm tra user có thuộc sự kiện trước khi trả dữ liệu.",
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = event_task_service.get_task_by_id(db, task_id)
    if not task:
        raise CustomException(status_code=status.HTTP_404_NOT_FOUND, detail="Công việc không tồn tại")
    _check_event_membership(db, task.event_id, current_user.id)
    return task


@router.patch(
    "/event-tasks/{task_id}",
    response_model=EventTaskResponse,
    summary="Cập nhật công việc sự kiện",
    description="Cập nhật các trường hợp lệ (PATCH), không ghi đè trường không gửi lên. "
                "OWNER cập nhật mọi task; MEMBER chỉ cập nhật task mình được giao.",
)
def update_task(
    task_id: int,
    task_in: EventTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = event_task_service.get_task_by_id(db, task_id)
    if not task:
        raise CustomException(status_code=status.HTTP_404_NOT_FOUND, detail="Công việc không tồn tại")
    _check_task_permission_for_update(db, task.event_id, current_user.id, task)
    updated_task, error_msg, sc = event_task_service.update_task(db, task, task_in, task.event_id)
    if error_msg:
        raise CustomException(status_code=sc, detail=error_msg)
    return updated_task


@router.delete(
    "/event-tasks/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa công việc sự kiện",
    description="Xóa công việc sự kiện. Chỉ OWNER của sự kiện mới có quyền xóa.",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = event_task_service.get_task_by_id(db, task_id)
    if not task:
        raise CustomException(status_code=status.HTTP_404_NOT_FOUND, detail="Công việc không tồn tại")
    _check_event_owner(db, task.event_id, current_user.id)
    event_task_service.delete_task(db, task)
    return {"detail": "Đã xóa công việc thành công"}


@router.patch(
    "/event-tasks/{task_id}/assign",
    response_model=EventTaskResponse,
    summary="Giao việc cho nhân sự",
    description="Gán assignee là nhân sự (staff) phụ trách trong ban tổ chức sự kiện. "
                "Không cho gán user ngoài sự kiện. Chỉ OWNER mới được giao việc.",
)
def assign_task(
    task_id: int,
    assignee_id: int = Query(..., description="ID nhân sự được giao việc (phải là thành viên sự kiện)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = event_task_service.get_task_by_id(db, task_id)
    if not task:
        raise CustomException(status_code=status.HTTP_404_NOT_FOUND, detail="Công việc không tồn tại")
    _check_event_owner(db, task.event_id, current_user.id)
    updated_task, error_msg, sc = event_task_service.assign_task(db, task, assignee_id, task.event_id)
    if error_msg:
        raise CustomException(status_code=sc, detail=error_msg)
    return updated_task


@router.post(
    "/event-tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo comment cho công việc",
    description="Thêm comment (trao đổi) cho công việc sự kiện. Chỉ thành viên sự kiện được tạo comment.",
)
def create_comment(
    task_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = event_task_service.get_task_by_id(db, task_id)
    if not task:
        raise CustomException(status_code=status.HTTP_404_NOT_FOUND, detail="Công việc không tồn tại")
    _check_event_membership(db, task.event_id, current_user.id)
    return comment_service.create_comment(db, task_id=task_id, user_id=current_user.id, comment_in=comment_in)


@router.get(
    "/event-tasks/{task_id}/comments",
    response_model=List[CommentResponse],
    summary="Danh sách comment của công việc",
    description="Lấy danh sách comment. Chỉ thành viên sự kiện được xem comment.",
)
def list_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = event_task_service.get_task_by_id(db, task_id)
    if not task:
        raise CustomException(status_code=status.HTTP_404_NOT_FOUND, detail="Công việc không tồn tại")
    _check_event_membership(db, task.event_id, current_user.id)
    return comment_service.get_comments_by_task(db, task_id=task_id)


@router.delete(
    "/event-tasks/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa comment",
    description="Xóa comment. Chỉ chủ comment hoặc OWNER sự kiện mới được xóa.",
)
def delete_comment(
    task_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    task = event_task_service.get_task_by_id(db, task_id)
    if not task:
        raise CustomException(status_code=status.HTTP_404_NOT_FOUND, detail="Công việc không tồn tại")
    comment = comment_service.get_comment_by_id(db, comment_id)
    if not comment or comment.task_id != task_id:
        raise CustomException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment không tồn tại")
    staff = _check_event_membership(db, task.event_id, current_user.id)
    if comment.user_id != current_user.id and staff.role != "OWNER":
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xóa comment này",
        )
    comment_service.delete_comment(db, comment)
    return {"detail": "Đã xóa comment thành công"}


