from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from learning.deps import get_learning_service
from learning.schemas.activity import (
    LastActivityResponse,
    UserLastActivityResponse,
)
from learning.services.learning_service import LearningService
from pbl6_common.deps import verify_internal_secret

router = APIRouter(
    prefix="/internal/learning",
    tags=["internal"],
    dependencies=[Depends(verify_internal_secret)],
)


@router.get(
    "/last-activity",
    response_model=LastActivityResponse | UserLastActivityResponse,
)
async def get_internal_last_activity(
    user_id: UUID | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=100000),
    service: LearningService = Depends(get_learning_service),
) -> LastActivityResponse | UserLastActivityResponse:
    """Internal API (T43): `GET /internal/learning/last-activity`.

    Queried by Notification Service (T14) daily study reminder cron.
    Returns one distinct row per user (`SELECT DISTINCT ON (user_id)`), and
    when `since` is supplied without an explicit `limit`, returns all users
    who studied since that timestamp without a 1000-row cap.
    """
    if user_id is not None:
        return await service.get_last_activity_for_user(user_id)
    effective_limit = limit if limit is not None else (None if since is not None else 1000)
    return await service.get_last_activities(since=since, limit=effective_limit)
