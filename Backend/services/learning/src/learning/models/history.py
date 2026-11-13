import uuid
from datetime import UTC, datetime

from pbl6_common.db import Base
from sqlalchemy import Column, DateTime, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID


class History(Base):
    __tablename__ = "histories"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="histories_user_lesson_key"),
        {"schema": "learning"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    lesson_id = Column(UUID(as_uuid=True), nullable=False)
    highest_score = Column(Float, nullable=False, default=0)
    completed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
