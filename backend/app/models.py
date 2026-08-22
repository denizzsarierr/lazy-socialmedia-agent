from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
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