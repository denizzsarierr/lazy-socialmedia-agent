import time
from datetime import datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.models import ScheduledPost
from app.queue import publish_queue


def schedule_due_posts() -> None:
    db = SessionLocal()

    try:
        now = datetime.utcnow()

        posts = db.scalars(
            select(ScheduledPost).where(
                ScheduledPost.status == "scheduled",
                ScheduledPost.scheduled_at <= now,
                ScheduledPost.job_id.is_(None),
            )
        ).all()

        for post in posts:
            print(
                f"Scheduling ScheduledPost #{post.id}"
            )

            job = publish_queue.enqueue(
                "app.jobs.process_scheduled_post",
                post.id,
            )

            post.job_id = job.id

            db.commit()

            print(
                f"ScheduledPost #{post.id} "
                f"queued as job {job.id}"
            )

    finally:
        db.close()


def scheduler_loop() -> None:
    print("Application scheduler started.")

    while True:
        try:
            schedule_due_posts()
        except Exception as exc:
            print(
                f"Scheduler error: {exc}"
            )

        time.sleep(10)