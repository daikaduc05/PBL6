import uuid
from datetime import datetime

from content.models.lesson import LessonAccess, LessonLevel, LessonStatus
from pydantic import BaseModel, ConfigDict, Field


class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: str | None = None
    level: LessonLevel = LessonLevel.EASY
    access: LessonAccess = LessonAccess.PUBLIC


class LessonCreate(LessonBase):
    category_id: uuid.UUID


class LessonUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    title: str | None = Field(None, min_length=1, max_length=255)
    body: str | None = None
    level: LessonLevel | None = None
    access: LessonAccess | None = None


class LessonResponse(LessonBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    status: LessonStatus
    created_at: datetime
    updated_at: datetime
