from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from learning.deps import get_learning_service
from learning.schemas.activity import (
    HistoryResponse,
    LastActivityResponse,
    UserLastActivityResponse,
)
from learning.services.learning_service import LearningService
from pbl6_common.deps import UserContext, get_current_user

router = APIRouter(tags=["learning"])


@router.get("/me/attempts", response_model=list[HistoryResponse])
@router.get("/learning/me/attempts", response_model=list[HistoryResponse])
async def get_my_attempts(
    user: UserContext = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
) -> list[HistoryResponse]:
    """Get the current authenticated user's quiz attempt history and highest scores."""
    return await service.get_user_history(UUID(user.user_id))


@router.get(
    "/learning/last-activity",
    response_model=LastActivityResponse | UserLastActivityResponse,
)
async def get_last_activity(
    user_id: UUID | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=5000),
    service: LearningService = Depends(get_learning_service),
) -> LastActivityResponse | UserLastActivityResponse:
    """Internal API (T43): get last activity timestamp of users or check if a user studied today.

    Used by Notification Service daily cron (20:00) to find students who haven't studied today.
    """
    if user_id is not None:
        return await service.get_last_activity_for_user(user_id)
    return await service.get_last_activities(since=since, limit=limit)
