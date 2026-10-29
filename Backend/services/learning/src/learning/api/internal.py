from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from learning.deps import get_learning_service
from learning.schemas.activity import (
    LastActivityResponse,
    UserLastActivityResponse,
)
from learning.services.learning_service import LearningService

router = APIRouter(prefix="/internal/learning", tags=["internal"])


@router.get(
    "/last-activity",
    response_model=LastActivityResponse | UserLastActivityResponse,
)
async def get_internal_last_activity(
    user_id: UUID | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=5000),
    service: LearningService = Depends(get_learning_service),
) -> LastActivityResponse | UserLastActivityResponse:
    """Internal API (T43): `GET /internal/learning/last-activity`.

    Queried by Notification Service (T14) daily study reminder cron.
    """
    if user_id is not None:
        return await service.get_last_activity_for_user(user_id)
    return await service.get_last_activities(since=since, limit=limit)
