import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from pbl6_common.db import Base
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID


class LessonLevel(str, enum.Enum):  # noqa: UP042
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class LessonAccess(str, enum.Enum):  # noqa: UP042
    PUBLIC = "public"
    VIP = "vip"


class LessonStatus(str, enum.Enum):  # noqa: UP042
    DRAFT = "draft"
    PENDING = "pending"
    PUBLISHED = "published"


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = {"schema": "content"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("content.categories.id"), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    level: Any = Column(
        SQLEnum(LessonLevel, name="lesson_level_enum", schema="content"),
        nullable=False,
        default=LessonLevel.EASY,
    )
    access: Any = Column(
        SQLEnum(LessonAccess, name="lesson_access_enum", schema="content"),
        nullable=False,
        default=LessonAccess.PUBLIC,
    )
    status: Any = Column(
        SQLEnum(LessonStatus, name="lesson_status_enum", schema="content"),
        nullable=False,
        default=LessonStatus.DRAFT,
    )
    search_vector = Column(TSVECTOR)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
