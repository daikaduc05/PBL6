import uuid
from datetime import UTC, datetime

from pbl6_common.db import Base
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = {"schema": "learning"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    parent_id = Column(
        UUID(as_uuid=True), ForeignKey("learning.comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    parent = relationship("Comment", remote_side=[id], backref="replies")
