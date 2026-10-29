from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    lesson_id: UUID
    highest_score: float
    completed_at: datetime


class UserActivityItem(BaseModel):
    user_id: UUID
    lesson_id: UUID
    highest_score: float
    last_activity_at: datetime


class LastActivityResponse(BaseModel):
    items: list[UserActivityItem]
    total: int


class UserLastActivityResponse(BaseModel):
    user_id: UUID
    last_activity_at: datetime | None = None
    lesson_id: UUID | None = None
    highest_score: float | None = None
    has_studied_today: bool = False
