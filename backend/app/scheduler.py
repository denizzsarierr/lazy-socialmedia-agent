import time
from datetime import datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.models import ScheduledPost, MediaAsset
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
            reel_asset = db.scalar(
                select(MediaAsset)
                .where(
                    MediaAsset.content_id == post.content_id,
                    MediaAsset.media_type == "reel",
                    MediaAsset.public_url.is_not(None),
                )
                .order_by(MediaAsset.id.desc())
            )

            if reel_asset is None:
                print(
                    f"ScheduledPost #{post.id} is due "
                    "but Reel media is not ready yet. "
                    "Skipping for now."
                )
                continue

            job = publish_queue.enqueue(
                "app.jobs.process_scheduled_post",
                post.id,
            )

            post.job_id = job.id

            db.commit()

            print(
                f"ScheduledPost #{post.id} queued "
                f"as job {job.id}."
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