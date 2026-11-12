from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FavoriteResponse(BaseModel):
    lesson_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoriteStatusResponse(BaseModel):
    lesson_id: UUID
    is_favorite: bool
