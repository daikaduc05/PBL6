from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="Nội dung bình luận")
    parent_id: UUID | None = Field(default=None, description="ID comment cha nếu là reply")


class CommentResponse(BaseModel):
    id: UUID
    lesson_id: UUID
    user_id: UUID
    parent_id: UUID | None = None
    content: str
    created_at: datetime
    replies: list[CommentResponse] = []

    model_config = {"from_attributes": True}
