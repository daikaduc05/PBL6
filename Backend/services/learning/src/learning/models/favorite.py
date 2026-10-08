from datetime import UTC, datetime

from pbl6_common.db import Base
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID


class FavoriteLesson(Base):
    __tablename__ = "favorite_lessons"
    __table_args__ = {"schema": "learning"}

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    lesson_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
