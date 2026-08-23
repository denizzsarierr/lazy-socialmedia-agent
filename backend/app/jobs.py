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
from app.services.media_storage import MediaStorage
from app.services.content_generator import ContentGenerator

MAX_ATTEMPTS = 3


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
            f"Processing ScheduledPost #{scheduled_post.id} "
            f"(attempt {scheduled_post.attempts}/{MAX_ATTEMPTS})"
        )

        storage = MediaStorage()

        media_urls = []

        for media in media_assets:
            if media.public_url:
                media_urls.append(media.public_url)
                continue

            public_url = storage.upload_image(
                media.file_path
            )

            media.public_url = public_url
            media_urls.append(public_url)

        db.commit()

        publisher = InstagramPublisher()

        result = publisher.publish_post(
            caption=content.caption,
            media_urls=media_urls,
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

            db.commit()

            print(
                f"ScheduledPost #{scheduled_post.id} "
                "published successfully."
            )

            return

        error_message = result["response"]

        if scheduled_post.attempts < MAX_ATTEMPTS:
            scheduled_post.status = "scheduled"
            scheduled_post.job_id = None
            scheduled_post.error_message = error_message

            publish_log = PublishLog(
                content_id=content.id,
                platform="instagram",
                status="failed",
                response=error_message,
            )

            db.add(publish_log)

            db.commit()

            print(
                f"ScheduledPost #{scheduled_post.id} failed. "
                f"Will retry. "
                f"Attempt {scheduled_post.attempts}/{MAX_ATTEMPTS}."
            )

        else:
            scheduled_post.status = "failed"
            scheduled_post.error_message = error_message

            publish_log = PublishLog(
                content_id=content.id,
                platform="instagram",
                status="failed",
                response=error_message,
            )

            db.add(publish_log)

            db.commit()

            print(
                f"ScheduledPost #{scheduled_post.id} "
                f"failed permanently after "
                f"{MAX_ATTEMPTS} attempts."
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

def generate_content_item() -> int:
    db = SessionLocal()

    try:
        recent_topics = db.scalars(
            select(ContentItem.topic)
            .where(ContentItem.topic.is_not(None))
            .order_by(ContentItem.created_at.desc())
            .limit(20)
        ).all()

        recent_categories = db.scalars(
            select(ContentItem.category)
            .where(ContentItem.category.is_not(None))
            .order_by(ContentItem.created_at.desc())
            .limit(12)
        ).all()

        categories = [
            "artificial_intelligence",
            "technology",
            "aviation",
        ]

        category_counts = {
            category: recent_categories.count(category)
            for category in categories
        }

        preferred_category = min(
            category_counts,
            key=category_counts.get,
        )

        print(
            f"Preferred category: {preferred_category}"
        )

        generator = ContentGenerator()

        generated = generator.generate_content(
            recent_topics=list(recent_topics),
            preferred_category=preferred_category,
        )

        content = ContentItem(
            content_type="post",
            category=generated["category"],
            topic=generated["topic"],
            caption=generated["caption"],
            status="draft",
        )

        db.add(content)
        db.commit()
        db.refresh(content)

        print(
            f"Generated ContentItem #{content.id}: "
            f"[{content.category}] {content.topic}"
        )

        return content.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()