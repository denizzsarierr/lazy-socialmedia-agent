from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    topic: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    caption: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    publish_logs: Mapped[list["PublishLog"]] = relationship(
    back_populates="content",
    cascade="all, delete-orphan",
    )

    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
    back_populates="content",
    cascade="all, delete-orphan",
    )

    media_assets: Mapped[list["MediaAsset"]] = relationship(
    back_populates="content",
    cascade="all, delete-orphan",
    )

    reel_contents: Mapped[list["ReelContent"]] = relationship(
    back_populates="content",
    cascade="all, delete-orphan",
    )

class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    content_id: Mapped[int] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    media_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    public_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    content: Mapped["ContentItem"] = relationship(
        back_populates="media_assets",
    )


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    content_id: Mapped[int] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="scheduled",
    )

    job_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    
    )

    attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    content: Mapped["ContentItem"] = relationship(
        back_populates="scheduled_posts",
    )

    

class PublishLog(Base):
    __tablename__ = "publish_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    content_id: Mapped[int] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="instagram",
    )

    platform_post_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    content: Mapped["ContentItem"] = relationship(
        back_populates="publish_logs",
    )

class ReelContent(Base):
    __tablename__ = "reel_contents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    content_id: Mapped[int] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    hook: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    script: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    visual_direction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    audio_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    audio_duration: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    content: Mapped["ContentItem"] = relationship(
        back_populates="reel_contents",
    )

    scenes: Mapped[list["ReelScene"]] = relationship(
        back_populates="reel",
        cascade="all, delete-orphan",
        order_by="ReelScene.clip_number",
    )

class ReelScene(Base):
    __tablename__ = "reel_scenes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    reel_id: Mapped[int] = mapped_column(
        ForeignKey("reel_contents.id", ondelete="CASCADE"),
        nullable=False,
    )

    clip_number: Mapped[int] = mapped_column(
        nullable=False,
    )

    presenter_action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    background_action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    camera_action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    video_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="planned",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    reel: Mapped["ReelContent"] = relationship(
        back_populates="scenes",
    )

    start_frame_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    end_frame_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )