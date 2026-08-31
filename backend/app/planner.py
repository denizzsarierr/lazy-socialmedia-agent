import time
from datetime import (
    date,
    datetime,
    time as dt_time,
    timedelta,
    timezone,
)
from zoneinfo import ZoneInfo
from rq.job import Job
from rq.exceptions import NoSuchJobError

from sqlalchemy import select

from app.database import SessionLocal
from app.jobs import (
    generate_content_item,
    prepare_reel_for_publish,
)
from app.models import ContentItem, ScheduledPost, MediaAsset
from app.queue import reel_queue


LOCAL_TIMEZONE = ZoneInfo("Europe/Warsaw")

POST_TIMES = [
    dt_time(hour=10, minute=0),
    dt_time(hour=18, minute=0),
]


def plan_daily_posts(
    target_date: date | None = None,
) -> None:
    db = SessionLocal()

    try:
        now_local = datetime.now(LOCAL_TIMEZONE)

        if target_date is None:
            target_date = now_local.date()

        print(
            f"Planning posts for {target_date} "
            f"({LOCAL_TIMEZONE.key})"
        )

        for post_time in POST_TIMES:
            scheduled_local = datetime.combine(
                target_date,
                post_time,
                tzinfo=LOCAL_TIMEZONE,
            )

            # If planning today, do not create a post
            # for a time that has already passed.
            if (
                target_date == now_local.date()
                and scheduled_local <= now_local
            ):
                print(
                    f"Skipping {scheduled_local:%H:%M}: "
                    "time already passed."
                )
                continue

            # Database currently stores timezone-naive UTC.
            scheduled_utc = (
                scheduled_local
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )

            existing_post = db.scalar(
                select(ScheduledPost).where(
                    ScheduledPost.scheduled_at
                    == scheduled_utc
                )
            )

            if existing_post is not None:
                print(
                    f"Post already scheduled for "
                    f"{scheduled_local:%H:%M}. "
                    f"ScheduledPost #{existing_post.id}"
                )
                continue

            # Generate the ContentItem.
            content_id = generate_content_item()

            content = db.get(
                ContentItem,
                content_id,
            )

            if content is None:
                raise RuntimeError(
                    f"Generated ContentItem "
                    f"#{content_id} could not be found."
                )

            content.status = "scheduled"

            scheduled_post = ScheduledPost(
                content_id=content.id,
                scheduled_at=scheduled_utc,
                status="scheduled",
            )

            db.add(scheduled_post)
            db.commit()
            db.refresh(scheduled_post)

            print(
                f"Scheduled ContentItem #{content.id} "
                f"as ScheduledPost #{scheduled_post.id} "
                f"for {scheduled_local:%Y-%m-%d %H:%M} "
                f"{LOCAL_TIMEZONE.key}"
            )

            # Generate the complete Reel in the worker.
            job = reel_queue.enqueue(
                prepare_reel_for_publish,
                content.id,
                job_timeout=1800,
            )

            scheduled_post.reel_job_id = job.id
            db.commit()

            print(
                f"Reel preparation queued for "
                f"ContentItem #{content.id}. "
                f"Job ID: {job.id}"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def recover_incomplete_reels() -> None:
    db = SessionLocal()

    try:

        now_utc = datetime.utcnow()
        posts = db.scalars(
            select(ScheduledPost).where(
                ScheduledPost.status == "scheduled",
                ScheduledPost.scheduled_at > now_utc,
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

            # Reel is already completely ready.
            if reel_asset is not None:
                continue

            active_job = False

            if post.reel_job_id:
                try:
                    job = Job.fetch(
                        post.reel_job_id,
                        connection=reel_queue.connection,
                    )

                    status = job.get_status(
                        refresh=True
                    )

                    if status in {
                        "queued",
                        "started",
                        "deferred",
                        "scheduled",
                    }:
                        active_job = True

                except NoSuchJobError:
                    active_job = False

            if active_job:
                print(
                    f"Reel preparation for "
                    f"ContentItem #{post.content_id} "
                    "is already active."
                )
                continue

            print(
                f"Recovering Reel preparation for "
                f"ContentItem #{post.content_id}..."
            )

            job = reel_queue.enqueue(
                prepare_reel_for_publish,
                post.content_id,
                job_timeout=1800,
            )

            post.reel_job_id = job.id
            db.commit()

            print(
                f"Recovery queued for ContentItem "
                f"#{post.content_id}. "
                f"Job ID: {job.id}"
            )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def planner_loop() -> None:
    print("Daily content planner started.")

    while True:
        try:
            now_local = datetime.now(
                LOCAL_TIMEZONE
            )

            today = now_local.date()
            tomorrow = (
                today
                + timedelta(days=1)
            )

            # Plan remaining slots for today.
            plan_daily_posts(
                target_date=today
            )

            # Pre-plan all slots for tomorrow.
            plan_daily_posts(
                target_date=tomorrow
            )

            recover_incomplete_reels()

        except Exception as exc:
            print(
                f"Daily planner error: {exc}"
            )

        time.sleep(300)