from datetime import datetime

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    ContentItem,
    MediaAsset,
    PublishLog,
    ScheduledPost,
    ReelContent,
)

from app.services.instagram import InstagramPublisher
from app.services.media_storage import MediaStorage
from app.services.content_generator import ContentGenerator

from app.services.audio_utils import get_audio_duration
from app.services.reel_script_generator import ReelScriptGenerator
from app.services.tts import TTSService

from app.services.ass_subtitle_generator import (
    generate_karaoke_ass,
)

from app.services.subtitle_alignment import (
    SubtitleAligner,
)

from app.services.subtitle_chunker import (
    chunk_words,
    merge_short_chunks,
)

from app.services.video.composer import (
    burn_subtitles,
)

from app.services.toru_renderer import (
    render_toru_video,
)


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

        # First check whether the Reel is actually ready.
        # Missing media is NOT a publishing attempt.
        reel_asset = db.scalar(
            select(MediaAsset)
            .where(
                MediaAsset.content_id == content.id,
                MediaAsset.media_type == "reel",
                MediaAsset.public_url.is_not(None),
            )
            .order_by(MediaAsset.id.desc())
        )

        if reel_asset is None:
            error_message = (
                f"Reel media for ContentItem "
                f"#{content.id} is not ready."
            )

            scheduled_post.status = "scheduled"
            scheduled_post.job_id = None
            scheduled_post.error_message = error_message

            db.commit()

            print(
                f"ScheduledPost #{scheduled_post.id} "
                "is waiting for Reel media. "
                f"Attempts remain "
                f"{scheduled_post.attempts}/{MAX_ATTEMPTS}."
            )

            return

        print(
            f"Using Reel MediaAsset #{reel_asset.id} "
            f"for ContentItem #{content.id}."
        )

        # From this point onward we are making a real
        # Instagram publishing attempt.
        scheduled_post.status = "processing"
        scheduled_post.attempts += 1

        db.commit()

        print(
            f"Processing ScheduledPost #{scheduled_post.id} "
            f"(attempt {scheduled_post.attempts}/{MAX_ATTEMPTS})"
        )

        publisher = InstagramPublisher()

        result = publisher.publish_reel(
            caption=content.caption,
            video_url=reel_asset.public_url,
            share_to_feed=True,
        )

        if result["success"]:
            published_at = datetime.utcnow()

            scheduled_post.status = "published"
            scheduled_post.published_at = published_at
            scheduled_post.error_message = None

            content.status = "published"
            content.published_at = published_at

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
                "published successfully as Reel."
            )

            return

        error_message = result["response"]

        publish_log = PublishLog(
            content_id=content.id,
            platform="instagram",
            status="failed",
            response=error_message,
        )

        db.add(publish_log)

        if scheduled_post.attempts < MAX_ATTEMPTS:
            scheduled_post.status = "scheduled"
            scheduled_post.job_id = None
            scheduled_post.error_message = error_message

            db.commit()

            print(
                f"ScheduledPost #{scheduled_post.id} failed. "
                "Will retry. "
                f"Attempt "
                f"{scheduled_post.attempts}/{MAX_ATTEMPTS}."
            )

        else:
            scheduled_post.status = "failed"
            scheduled_post.error_message = error_message

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

def generate_reel_content(content_id: int) -> int:
    db = SessionLocal()

    try:
        content = db.get(
            ContentItem,
            content_id,
        )

        if content is None:
            raise ValueError(
                f"ContentItem #{content_id} not found."
            )

        existing = db.scalar(
            select(ReelContent).where(
                ReelContent.content_id == content_id
            )
        )

        if existing is not None:
            print(
                f"ReelContent #{existing.id} already exists "
                f"for ContentItem #{content_id}."
            )

            return existing.id

        generator = ReelScriptGenerator()

        generated = generator.generate(
            category=content.category,
            topic=content.topic,
            caption=content.caption,
        )

        reel = ReelContent(
            content_id=content.id,
            hook=generated["hook"],
            script=generated["script"],
            visual_direction=generated["visual_direction"],
            status="script_ready",
        )

        db.add(reel)
        db.commit()
        db.refresh(reel)

        print(
            f"Generated ReelContent #{reel.id} "
            f"for ContentItem #{content.id}."
        )

        return reel.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def generate_reel_audio(reel_id: int) -> str:
    db = SessionLocal()

    try:
        reel = db.get(
            ReelContent,
            reel_id,
        )

        if reel is None:
            raise ValueError(
                f"ReelContent #{reel_id} not found."
            )

        if reel.audio_path:
            print(
                f"Audio already exists: {reel.audio_path}"
            )
            return reel.audio_path

        output_path = (
            f"/app/generated/reels/"
            f"reel_{reel.id}/voice.mp3"
        )

        tts = TTSService()

        audio_path = tts.generate(
            text=reel.script,
            output_path=output_path,
        )

        duration = get_audio_duration(
            audio_path
        )

        reel.audio_path = audio_path
        reel.audio_duration = duration
        reel.status = "audio_ready"

        db.commit()

        print(
            f"Generated audio for ReelContent #{reel.id}: "
            f"{duration:.2f}s"
        )

        return audio_path

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def build_reel_pipeline(content_id: int) -> str:

    db = SessionLocal()

    try:
        # 1. ReelContent
        reel = db.scalar(
            select(ReelContent).where(
                ReelContent.content_id == content_id
            )
        )

        if reel is None:
            db.close()

            reel_id = generate_reel_content(
                content_id
            )

            db = SessionLocal()

            reel = db.get(
                ReelContent,
                reel_id,
            )

        if reel is None:
            raise RuntimeError(
                f"Could not create ReelContent "
                f"for ContentItem #{content_id}."
            )

        reel_id = reel.id

        print(
            f"Building ReelContent #{reel_id} "
            f"for ContentItem #{content_id}."
        )

        # 2. TTS audio
        if (
            not reel.audio_path
            or reel.audio_duration is None
        ):
            db.close()

            generate_reel_audio(
                reel_id
            )

            db = SessionLocal()

            reel = db.get(
                ReelContent,
                reel_id,
            )

        if reel is None:
            raise RuntimeError(
                f"ReelContent #{reel_id} "
                f"could not be reloaded."
            )

        if not reel.audio_path:
            raise RuntimeError(
                f"ReelContent #{reel_id} "
                f"has no audio."
            )

        if not reel.script:
            raise RuntimeError(
                f"ReelContent #{reel_id} "
                f"has no script."
            )

        reel_dir = (
            f"/app/generated/reels/"
            f"reel_{reel_id}"
        )

        raw_final_path = (
            f"{reel_dir}/final_reel.mp4"
        )

        final_path = (
            f"{reel_dir}/"
            f"final_reel_subtitled.mp4"
        )

        ass_path = (
            f"{reel_dir}/subtitles.ass"
        )

        # 3. Whisper word-level timestamps
        aligner = SubtitleAligner()

        words = aligner.align_words(
            reel.audio_path
        )

        print(
            f"Detected {len(words)} "
            f"spoken words."
        )

        # 4. Toru animation + audio
        render_toru_video(
            audio_path=reel.audio_path,
            script=reel.script,
            words=words,
            output_path=raw_final_path,
        )

        print(
            f"Rendered Toru Reel: "
            f"{raw_final_path}"
        )

        # 5. Subtitle chunks
        chunks = chunk_words(
            words,
            max_words=5,
            max_duration=2.5,
            max_gap=0.45,
        )

        chunks = merge_short_chunks(
            chunks,
            min_words=2,
        )

        # 6. ASS karaoke subtitles
        generate_karaoke_ass(
            chunks,
            ass_path,
        )

        # 7. Subtitle burn
        burn_subtitles(
            video_path=raw_final_path,
            ass_path=ass_path,
            output_path=final_path,
        )

        reel.status = "ready"

        db.commit()

        print(
            f"ReelContent #{reel_id} "
            f"completed."
        )

        print(
            f"Final video: "
            f"{final_path}"
        )

        return final_path

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def upload_final_reel(
    reel_id: int,
    final_path: str,
    ) -> int:
    db = SessionLocal()

    try:
        reel = db.get(
            ReelContent,
            reel_id,
        )

        if reel is None:
            raise ValueError(
                f"ReelContent #{reel_id} not found."
            )


        existing_asset = db.scalar(
            select(MediaAsset).where(
                MediaAsset.content_id == reel.content_id,
                MediaAsset.media_type == "reel",
            )
        )

        if (
            existing_asset is not None
            and existing_asset.public_url
        ):
            print(
                f"Reel MediaAsset #{existing_asset.id} "
                "already exists. Skipping upload."
            )

            return existing_asset.id

        storage = MediaStorage()

        public_url = storage.upload_video(
            final_path
        )

        if existing_asset is None:
            asset = MediaAsset(
                content_id=reel.content_id,
                media_type="reel",
                file_path=final_path,
                public_url=public_url,
            )

            db.add(asset)

        else:
            asset = existing_asset
            asset.file_path = final_path
            asset.public_url = public_url

        db.commit()
        db.refresh(asset)

        print(
            f"Final Reel uploaded as "
            f"MediaAsset #{asset.id}"
        )

        print(
            f"Public URL: {asset.public_url}"
        )

        return asset.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def prepare_reel_for_publish(content_id: int) -> int:
    """
    Build the complete Reel and upload the final video to Cloudinary.

    Returns the MediaAsset id.
    """
    print(
        f"Preparing Reel for ContentItem #{content_id}..."
    )

    final_path = build_reel_pipeline(content_id)

    db = SessionLocal()

    try:
        reel = (
            db.query(ReelContent)
            .filter(ReelContent.content_id == content_id)
            .order_by(ReelContent.id.desc())
            .first()
        )

        if reel is None:
            raise RuntimeError(
                f"ReelContent for ContentItem "
                f"#{content_id} could not be found."
            )

        reel_id = reel.id

    finally:
        db.close()

    asset_id = upload_final_reel(
        reel_id=reel_id,
        final_path=final_path,
    )

    print(
        f"Reel for ContentItem #{content_id} ready. "
        f"MediaAsset #{asset_id}"
    )

    return asset_id