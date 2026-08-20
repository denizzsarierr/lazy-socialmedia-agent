from datetime import datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    ContentItem,
    MediaAsset,
    PublishLog,
    ScheduledPost,
)
from app.services.instagram import InstagramPublisher


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

        if scheduled_post.status != "scheduled":
            print(
                f"ScheduledPost #{scheduled_post.id} "
                f"has status '{scheduled_post.status}'. "
                "Skipping."
            )
            return

        content = db.scalar(
            select(ContentItem).where(
                ContentItem.id == scheduled_post.content_id
            )
        )

        if content is None:
            raise ValueError(
                f"ContentItem #{scheduled_post.content_id} not found."
            )

        media_assets = db.scalars(
            select(MediaAsset).where(
                MediaAsset.content_id == content.id
            )
        ).all()

        scheduled_post.status = "processing"
        scheduled_post.attempts += 1

        db.commit()

        print(
            f"Processing ScheduledPost #{scheduled_post.id}"
        )

        publisher = InstagramPublisher()

        result = publisher.publish_post(
            caption=content.caption,
            media_paths=[
                media.file_path
                for media in media_assets
            ],
        )

        if result["success"]:
            scheduled_post.status = "published"
            scheduled_post.published_at = datetime.utcnow()

            content.status = "published"
            content.published_at = datetime.utcnow()

            publish_log = PublishLog(
                content_id=content.id,
                platform="instagram",
                platform_post_id=result["platform_post_id"],
                status="success",
                response=result["response"],
            )

            db.add(publish_log)

        else:
            scheduled_post.status = "failed"
            scheduled_post.error_message = result["response"]

            publish_log = PublishLog(
                content_id=content.id,
                platform="instagram",
                status="failed",
                response=result["response"],
            )

            db.add(publish_log)

        db.commit()

        print(
            f"ScheduledPost #{scheduled_post.id} "
            f"completed with status '{scheduled_post.status}'."
        )

    except Exception as exc:
        db.rollback()

        print(
            f"Failed to process ScheduledPost "
            f"#{scheduled_post_id}: {exc}"
        )

        raise

    finally:
        db.close()