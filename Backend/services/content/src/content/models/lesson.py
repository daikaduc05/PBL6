import uuid
from datetime import datetime, timezone
import enum

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from pbl6_common.db import Base

class LessonLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class LessonAccess(str, enum.Enum):
    PUBLIC = "public"
    VIP = "vip"

class LessonStatus(str, enum.Enum):
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
    level = Column(SQLEnum(LessonLevel, name="lesson_level_enum", schema="content"), nullable=False, default=LessonLevel.EASY)
    access = Column(SQLEnum(LessonAccess, name="lesson_access_enum", schema="content"), nullable=False, default=LessonAccess.PUBLIC)
    status = Column(SQLEnum(LessonStatus, name="lesson_status_enum", schema="content"), nullable=False, default=LessonStatus.DRAFT)
    search_vector = Column(TSVECTOR)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
