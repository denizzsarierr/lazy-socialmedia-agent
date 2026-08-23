import time
from datetime import date, datetime, time as dt_time, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.database import SessionLocal
from app.jobs import generate_content_item
from app.models import ContentItem, ScheduledPost


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

            # Our current DB columns are timezone-naive,
            # so store UTC without tzinfo.
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

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def planner_loop() -> None:
    print("Daily content planner started.")

    while True:
        try:
            plan_daily_posts()
        except Exception as exc:
            print(
                f"Daily planner error: {exc}"
            )

        # Check every 5 minutes.
        # Duplicate protection prevents recreating posts.
        time.sleep(300)