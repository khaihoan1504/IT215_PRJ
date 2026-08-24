from db.database import SessionLocal, engine, Base
from models.user import User
from models.event import Event
from models.event_staff import EventStaff
from models.event_task import EventTask
from core.security import get_password_hash
import models


def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).first():
            user1 = User(
                email="admin@example.com",
                hashed_password=get_password_hash("123456"),
                full_name="Admin",
                role="ADMIN",
            )
            user2 = User(
                email="staff@example.com",
                hashed_password=get_password_hash("123456"),
                full_name="Staff",
                role="USER",
            )
            db.add_all([user1, user2])
            db.commit()

            event = Event(title="Event 1", description="Description", creator_id=user1.id)
            db.add(event)
            db.commit()

            staff = EventStaff(event_id=event.id, user_id=user1.id, role="OWNER")
            db.add(staff)
            staff2 = EventStaff(event_id=event.id, user_id=user2.id, role="MEMBER")
            db.add(staff2)
            db.commit()

            task = EventTask(
                event_id=event.id,
                assignee_id=user2.id,
                title="Task 1",
                description="Do something",
                status="TODO",
                priority="MEDIUM",
            )
            db.add(task)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
    print("Seed data completed!")

