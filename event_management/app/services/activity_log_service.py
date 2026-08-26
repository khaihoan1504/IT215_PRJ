from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.activity_log import ActivityLog


def log_activity(
    db: Session,
    user_id: int,
    action: str,
    target_type: str,
    target_id: Optional[int] = None,
    detail: Optional[str] = None,
) -> ActivityLog:
    log = ActivityLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_event_activity_logs(
    db: Session,
    event_id: int,
    skip: int = 0,
    limit: int = 50,
) -> List[ActivityLog]:
    return (
        db.query(ActivityLog)
        .options(joinedload(ActivityLog.user))
        .filter(
            ActivityLog.target_type == "EVENT",
            ActivityLog.target_id == event_id,
        )
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

