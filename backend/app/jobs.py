import os
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

from app.models import ContentItem, ReelContent, ReelScene
from app.services.audio_utils import get_audio_duration
from app.services.reel_script_generator import ReelScriptGenerator
from app.services.tts import TTSService

from app.services.video.clip_planner import plan_video_clips
from app.services.video.scene_planner import ScenePlanner
from app.services.video.prompt_builder import build_scene_video_prompt

from app.services.video.downloader import download_video
from app.services.video.frame_utils import extract_last_frame, extract_frame_before_end
from app.services.video.runway import RunwayVideoGenerator

from app.services.ass_subtitle_generator import generate_karaoke_ass
from app.services.subtitle_alignment import SubtitleAligner
from app.services.subtitle_chunker import (
    chunk_words,
    merge_short_chunks,
)
from app.services.video.composer import (
    burn_subtitles,
    compose_reel,
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

        reel_asset = db.scalar(
            select(MediaAsset)
            .where(
                MediaAsset.content_id == content.id,
                MediaAsset.media_type == "reel",
                MediaAsset.public_url.is_not(None),
            )
            .order_by(MediaAsset.id.desc())
        )

        scheduled_post.status = "processing"
        scheduled_post.attempts += 1

        db.commit()

        print(
            f"Processing ScheduledPost #{scheduled_post.id} "
            f"(attempt {scheduled_post.attempts}/{MAX_ATTEMPTS})"
        )

        if reel_asset is None:
            error_message = (
                f"Reel media for ContentItem "
                f"#{content.id} is not ready."
            )

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
                    f"ScheduledPost #{scheduled_post.id} "
                    "cannot be published yet. "
                    f"{error_message} "
                    f"Attempt "
                    f"{scheduled_post.attempts}/{MAX_ATTEMPTS}."
                )

                return

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

            return

        print(
            f"Using Reel MediaAsset #{reel_asset.id} "
            f"for ContentItem #{content.id}."
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
                f"Attempt "
                f"{scheduled_post.attempts}/{MAX_ATTEMPTS}."
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

def generate_reel_scenes(reel_id: int) -> list[int]:
    db = SessionLocal()

    try:
        reel = db.get(ReelContent, reel_id)

        if reel is None:
            raise ValueError(
                f"ReelContent #{reel_id} not found."
            )

        if reel.audio_duration is None:
            raise ValueError(
                f"ReelContent #{reel_id} has no audio duration."
            )

        existing_scenes = db.scalars(
            select(ReelScene)
            .where(ReelScene.reel_id == reel_id)
            .order_by(ReelScene.clip_number)
        ).all()

        if existing_scenes:
            print(
                f"ReelContent #{reel_id} already has "
                f"{len(existing_scenes)} scenes."
            )

            return [scene.id for scene in existing_scenes]

        content = db.get(
            ContentItem,
            reel.content_id,
        )

        if content is None:
            raise ValueError(
                f"ContentItem #{reel.content_id} not found."
            )

        clip_plan = plan_video_clips(
            reel.audio_duration
        )

        planner = ScenePlanner()

        planned_scenes = planner.plan(
            topic=content.topic,
            script=reel.script,
            visual_direction=reel.visual_direction,
            clip_count=clip_plan.clip_count,
        )

        scene_ids = []

        for planned in planned_scenes:
            prompt = build_scene_video_prompt(
                topic=content.topic,
                scene=planned,
            )

            scene = ReelScene(
                reel_id=reel.id,
                clip_number=planned["clip_number"],
                presenter_action=planned["presenter_action"],
                background_action=planned["background_action"],
                camera_action=planned["camera_action"],
                prompt=prompt,
                status="planned",
            )

            db.add(scene)
            db.flush()

            scene_ids.append(scene.id)

        reel.status = "scenes_ready"

        db.commit()

        print(
            f"Generated {len(scene_ids)} scenes "
            f"for ReelContent #{reel.id}."
        )

        return scene_ids

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def generate_reel_videos(reel_id: int) -> list[str]:
    db = SessionLocal()

    try:
        reel = db.get(ReelContent, reel_id)

        if reel is None:
            raise ValueError(
                f"ReelContent #{reel_id} not found."
            )

        anchor_url = os.getenv(
            "TORU_REFERENCE_IMAGE_URL"
        )

        if not anchor_url:
            raise ValueError(
                "TORU_REFERENCE_IMAGE_URL is not configured."
            )

        scenes = db.scalars(
            select(ReelScene)
            .where(ReelScene.reel_id == reel_id)
            .order_by(ReelScene.clip_number)
        ).all()

        if not scenes:
            raise ValueError(
                f"ReelContent #{reel_id} has no scenes."
            )

        generator = RunwayVideoGenerator()
        storage = MediaStorage()

        video_paths = []

        # Clip 1 canonical Toru reference ile başlar.
        # Sonraki clip'lerde bir önceki clip'in end_frame_url
        # değeri kullanılacak.
        current_reference = anchor_url

        for scene in scenes:

            # Daha önce başarıyla üretilen clip'lere dokunma.
            if (
                scene.status == "video_ready"
                and scene.video_path
            ):
                print(
                    f"Clip {scene.clip_number} already exists. "
                    "Skipping."
                )

                video_paths.append(
                    scene.video_path
                )

                # Bir sonraki clip bu clip'in gerçek
                # son karesinden devam edecek.
                if scene.end_frame_url:
                    current_reference = (
                        scene.end_frame_url
                    )

                continue

            if not scene.prompt:
                raise ValueError(
                    f"Clip {scene.clip_number} "
                    "has no prompt."
                )

            print(
                f"Generating clip "
                f"{scene.clip_number}/{len(scenes)}..."
            )

            print(
                f"Reference frame: "
                f"{current_reference}"
            )

            try:
                # Recovery frame kullanmıyoruz.
                # Scene hangi reference ile gerçekten
                # üretildiyse DB'ye onu kaydediyoruz.
                scene.status = "generating"
                scene.start_frame_url = (
                    current_reference
                )
                db.commit()

                # TEK RUNWAY DENEMESİ
                video_url = generator.generate(
                    reference_image_url=(
                        current_reference
                    ),
                    prompt=scene.prompt,
                    duration=5,
                )

                reel_dir = (
                    f"/app/generated/reels/"
                    f"reel_{reel.id}"
                )

                video_path = (
                    f"{reel_dir}/clips/"
                    f"clip_{scene.clip_number:02d}.mp4"
                )

                download_video(
                    video_url,
                    video_path,
                )

                last_frame_path = (
                    f"{reel_dir}/frames/"
                    f"clip_{scene.clip_number:02d}"
                    "_last.jpg"
                )

                extract_last_frame(
                    video_path,
                    last_frame_path,
                )

                last_frame_url = (
                    storage.upload_image(
                        last_frame_path
                    )
                )

                scene.video_path = video_path
                scene.end_frame_url = (
                    last_frame_url
                )
                scene.status = "video_ready"

                db.commit()

                video_paths.append(
                    video_path
                )

                # Sonraki clip artık bu clip'in
                # gerçek son karesinden devam eder.
                current_reference = (
                    last_frame_url
                )

                print(
                    f"Clip {scene.clip_number} ready."
                )

                print(
                    f"Next reference: "
                    f"{last_frame_url}"
                )

            except Exception as exc:
                db.rollback()

                failed_scene = db.get(
                    ReelScene,
                    scene.id,
                )

                if failed_scene is not None:
                    failed_scene.status = "failed"
                    db.commit()

                print(
                    f"Clip {scene.clip_number} "
                    f"failed: {exc}"
                )

                # Bir clip başarısız olursa Reel'i
                # burada durduruyoruz.
                break

        remaining_scene = db.scalar(
            select(ReelScene)
            .where(
                ReelScene.reel_id == reel_id,
                ReelScene.status
                != "video_ready",
            )
            .limit(1)
        )

        if remaining_scene is None:
            reel.status = "videos_ready"

            print(
                f"All videos for ReelContent "
                f"#{reel.id} are ready."
            )

        else:
            reel.status = "video_incomplete"

            print(
                f"ReelContent #{reel.id} "
                "still has unfinished clips."
            )

        db.commit()

        return video_paths

    finally:
        db.close()

def build_reel_pipeline(content_id: int) -> str:

    db = SessionLocal()

    try:
        # 1. ReelContent oluştur / mevcut olanı kullan
        reel = db.scalar(
            select(ReelContent).where(
                ReelContent.content_id == content_id
            )
        )

        if reel is None:
            db.close()
            reel_id = generate_reel_content(content_id)
            db = SessionLocal()
            reel = db.get(ReelContent, reel_id)

        if reel is None:
            raise RuntimeError(
                f"Could not create ReelContent for ContentItem #{content_id}."
            )

        reel_id = reel.id

        print(
            f"Building ReelContent #{reel_id} "
            f"for ContentItem #{content_id}."
        )

        # 2. Audio
        if not reel.audio_path or reel.audio_duration is None:
            db.close()
            generate_reel_audio(reel_id)
            db = SessionLocal()
            reel = db.get(ReelContent, reel_id)

        # 3. Scene planları
        existing_scenes = db.scalars(
            select(ReelScene).where(
                ReelScene.reel_id == reel_id
            )
        ).all()

        if not existing_scenes:
            db.close()
            generate_reel_scenes(reel_id)
            db = SessionLocal()

        # 4. Runway videoları
        db.close()

        generate_reel_videos(reel_id)

        db = SessionLocal()

        reel = db.get(
            ReelContent,
            reel_id,
        )

        scenes = db.scalars(
            select(ReelScene)
            .where(
                ReelScene.reel_id == reel_id
            )
            .order_by(
                ReelScene.clip_number
            )
        ).all()

        incomplete_scene = next(
            (
                scene
                for scene in scenes
                if (
                    scene.status != "video_ready"
                    or not scene.video_path
                )
            ),
            None,
        )

        if incomplete_scene is not None:
            raise RuntimeError(
                f"ReelContent #{reel_id} has unfinished video clips."
            )

        clip_paths = [
            scene.video_path
            for scene in scenes
        ]

        reel_dir = (
            f"/app/generated/reels/"
            f"reel_{reel_id}"
        )

        # 5. Klipleri birleştir + Marin audio
        raw_final_path = (
            f"{reel_dir}/final_reel.mp4"
        )

        compose_reel(
            clip_paths=clip_paths,
            audio_path=reel.audio_path,
            output_path=raw_final_path,
        )

        print(
            f"Composed Reel: {raw_final_path}"
        )

        # 6. Word-level timestamp
        aligner = SubtitleAligner()

        words = aligner.align_words(
            reel.audio_path
        )

        # 7. Subtitle chunks
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

        # 8. ASS karaoke
        ass_path = (
            f"{reel_dir}/subtitles.ass"
        )

        generate_karaoke_ass(
            chunks,
            ass_path,
        )

        # 9. Subtitle burn
        final_path = (
            f"{reel_dir}/final_reel_subtitled.mp4"
        )

        burn_subtitles(
            video_path=raw_final_path,
            ass_path=ass_path,
            output_path=final_path,
        )

        reel.status = "ready"

        db.commit()

        print(
            f"ReelContent #{reel_id} completed."
        )

        print(
            f"Final video: {final_path}"
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