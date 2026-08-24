from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc

from models.event_task import EventTask
from models.event_staff import EventStaff
from schemas.event_task import EventTaskCreate, EventTaskUpdate

VALID_STATUSES = {"TODO", "IN_PROGRESS", "DONE"}
VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}
VALID_SORT_FIELDS = {"created_at", "due_date", "priority", "status", "title"}


def create_task(
    db: Session, event_id: int, task_in: EventTaskCreate
) -> Tuple[Optional[EventTask], Optional[str], int]:
    if task_in.assignee_id is not None:
        staff = (
            db.query(EventStaff)
            .filter(
                EventStaff.event_id == event_id,
                EventStaff.user_id == task_in.assignee_id,
            )
            .first()
        )
        if not staff:
            return None, "Người được giao việc phải là thành viên của sự kiện", 400

    new_task = EventTask(
        event_id=event_id,
        title=task_in.title,
        description=task_in.description,
        assignee_id=task_in.assignee_id,
        status=task_in.status.value if task_in.status else "TODO",
        priority=task_in.priority.value if task_in.priority else "MEDIUM",
        due_date=task_in.due_date,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task, None, 201


def get_task_by_id(db: Session, task_id: int) -> Optional[EventTask]:
    return (
        db.query(EventTask)
        .options(
            joinedload(EventTask.assignee),
            joinedload(EventTask.event),
            joinedload(EventTask.comments),
            joinedload(EventTask.attachments),
        )
        .filter(EventTask.id == task_id)
        .first()
    )


def get_tasks_by_event(
    db: Session,
    event_id: int,
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 20,
) -> List[EventTask]:
    query = (
        db.query(EventTask)
        .options(joinedload(EventTask.assignee))
        .filter(EventTask.event_id == event_id)
    )
    if status and status in VALID_STATUSES:
        query = query.filter(EventTask.status == status)
    if priority and priority in VALID_PRIORITIES:
        query = query.filter(EventTask.priority == priority)
    if assignee_id is not None:
        query = query.filter(EventTask.assignee_id == assignee_id)
    if search:
        query = query.filter(EventTask.title.ilike(f"%{search}%"))

    if sort_by not in VALID_SORT_FIELDS:
        sort_by = "created_at"
    sort_column = getattr(EventTask, sort_by, EventTask.created_at)

    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    return query.offset(skip).limit(limit).all()


def update_task(
    db: Session, task: EventTask, task_in: EventTaskUpdate, event_id: int
) -> Tuple[Optional[EventTask], Optional[str], int]:
    update_data = task_in.model_dump(exclude_unset=True)

    if "assignee_id" in update_data and update_data["assignee_id"] is not None:
        staff = (
            db.query(EventStaff)
            .filter(
                EventStaff.event_id == event_id,
                EventStaff.user_id == update_data["assignee_id"],
            )
            .first()
        )
        if not staff:
            return None, "Người được giao việc phải là thành viên của sự kiện", 400

    if "status" in update_data and update_data["status"] is not None:
        status_val = update_data["status"]
        if hasattr(status_val, "value"):
            status_val = status_val.value
        if status_val not in VALID_STATUSES:
            return None, f"Trạng thái không hợp lệ. Cho phép: {', '.join(VALID_STATUSES)}", 400
        update_data["status"] = status_val

    if "priority" in update_data and update_data["priority"] is not None:
        priority_val = update_data["priority"]
        if hasattr(priority_val, "value"):
            priority_val = priority_val.value
        if priority_val not in VALID_PRIORITIES:
            return None, f"Mức ưu tiên không hợp lệ. Cho phép: {', '.join(VALID_PRIORITIES)}", 400
        update_data["priority"] = priority_val

    for key, value in update_data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task, None, 200


def delete_task(db: Session, task: EventTask) -> None:
    db.delete(task)
    db.commit()


def assign_task(
    db: Session, task: EventTask, assignee_id: int, event_id: int
) -> Tuple[Optional[EventTask], Optional[str], int]:
    staff = (
        db.query(EventStaff)
        .filter(
            EventStaff.event_id == event_id,
            EventStaff.user_id == assignee_id,
        )
        .first()
    )
    if not staff:
        return None, "Người được giao việc phải là thành viên (staff) trong ban tổ chức sự kiện", 400

    task.assignee_id = assignee_id
    db.commit()
    db.refresh(task)
    return task, None, 200

