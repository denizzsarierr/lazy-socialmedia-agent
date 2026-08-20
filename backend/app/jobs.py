from sqlalchemy import select

from app.database import SessionLocal
from app.models import ScheduledPost


def test_job(message: str) -> str:
    print(f"TEST JOB: {message}")
    return f"Processed: {message}"

def process_scheduled_post(scheduled_post_id: int) -> None:
    db = SessionLocal()

    try:
        scheduled_post = db.scalar(
            select(ScheduledPost).where(
                ScheduledPost.id == scheduled_post_id
            )
        )

        if scheduled_post is None:
            print(
                f"ScheduledPost #{scheduled_post_id} not found."
            )
            return

        print(
            f"ScheduledPost #{scheduled_post.id} found."
        )

        print(
            f"Content ID: {scheduled_post.content_id}"
        )

        print(
            f"Scheduled at: {scheduled_post.scheduled_at}"
        )

        print(
            f"Status: {scheduled_post.status}"
        )

    finally:
        db.close()