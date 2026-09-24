import uuid
import enum
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from pbl6_common.db import Base

class MediaKind(str, enum.Enum):
    AUDIO = "audio"
    IMAGE = "image"

class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = {"schema": "content"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("content.lessons.id"), nullable=False)
    kind = Column(SQLEnum(MediaKind, name="media_kind_enum", schema="content"), nullable=False)
    s3_key = Column(String, nullable=False)
    cdn_url = Column(String, nullable=False)
    bytes = Column(Integer, nullable=False)
