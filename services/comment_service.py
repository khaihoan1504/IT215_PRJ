from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from models.comment import TaskComment
from schemas.comment import CommentCreate, CommentUpdate
def create_comment(
    db: Session, task_id: int, user_id: int, comment_in: CommentCreate
) -> TaskComment:
    new_comment = TaskComment(
        task_id=task_id,
        user_id=user_id,
        content=comment_in.content,
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment
def get_comments_by_task(db: Session, task_id: int) -> List[TaskComment]:
    return (
        db.query(TaskComment)
        .options(joinedload(TaskComment.user))
        .filter(TaskComment.task_id == task_id)
        .order_by(TaskComment.created_at.asc())
        .all()
    )
def get_comment_by_id(db: Session, comment_id: int) -> Optional[TaskComment]:
    return db.query(TaskComment).filter(TaskComment.id == comment_id).first()
def update_comment(db: Session, comment: TaskComment, comment_in: CommentUpdate) -> TaskComment:
    comment.content = comment_in.content
    db.commit()
    db.refresh(comment)
    return comment
def delete_comment(db: Session, comment: TaskComment) -> None:
    db.delete(comment)
    db.commit()
