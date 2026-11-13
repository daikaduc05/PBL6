from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from learning.deps import get_favorite_service
from learning.schemas.favorite import FavoriteResponse, FavoriteStatusResponse
from learning.services.favorite_service import FavoriteService
from pbl6_common.deps import UserContext, get_current_user

router = APIRouter(tags=["favorites"])


@router.get("/me/favorites", response_model=list[FavoriteResponse])
@router.get("/learning/me/favorites", response_model=list[FavoriteResponse])
async def get_my_favorites(
    user: UserContext = Depends(get_current_user),
    service: FavoriteService = Depends(get_favorite_service),
) -> list[FavoriteResponse]:
    """Get list of favorite lessons for the authenticated student (T49)."""
    return await service.get_user_favorites(UUID(user.user_id))


@router.get("/lessons/{lesson_id}/favorite", response_model=FavoriteStatusResponse)
async def check_favorite_status(
    lesson_id: UUID,
    user: UserContext = Depends(get_current_user),
    service: FavoriteService = Depends(get_favorite_service),
) -> FavoriteStatusResponse:
    """Check if the lesson is in current user's favorites (T49)."""
    return await service.check_favorite(UUID(user.user_id), lesson_id)


@router.post(
    "/lessons/{lesson_id}/favorite",
    response_model=FavoriteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_favorite_lesson(
    lesson_id: UUID,
    user: UserContext = Depends(get_current_user),
    service: FavoriteService = Depends(get_favorite_service),
) -> FavoriteResponse:
    """Add a lesson to current user's favorites (T49)."""
    return await service.add_favorite(UUID(user.user_id), lesson_id)


@router.delete(
    "/lessons/{lesson_id}/favorite",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_favorite_lesson(
    lesson_id: UUID,
    user: UserContext = Depends(get_current_user),
    service: FavoriteService = Depends(get_favorite_service),
) -> None:
    """Remove a lesson from current user's favorites (T49)."""
    await service.remove_favorite(UUID(user.user_id), lesson_id)
