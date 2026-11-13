from __future__ import annotations

from uuid import UUID

from learning.repositories.favorite_repository import FavoriteRepository
from learning.schemas.favorite import FavoriteResponse, FavoriteStatusResponse


class FavoriteService:
    def __init__(self, repo: FavoriteRepository):
        self.repo = repo

    async def get_user_favorites(self, user_id: UUID) -> list[FavoriteResponse]:
        items = await self.repo.list_by_user(user_id)
        return [
            FavoriteResponse(lesson_id=item.lesson_id, created_at=item.created_at) for item in items
        ]

    async def check_favorite(self, user_id: UUID, lesson_id: UUID) -> FavoriteStatusResponse:
        fav = await self.repo.get_by_user_and_lesson(user_id, lesson_id)
        return FavoriteStatusResponse(
            lesson_id=lesson_id,
            is_favorite=fav is not None,
        )

    async def add_favorite(self, user_id: UUID, lesson_id: UUID) -> FavoriteResponse:
        fav = await self.repo.add(user_id, lesson_id)
        return FavoriteResponse(lesson_id=fav.lesson_id, created_at=fav.created_at)

    async def remove_favorite(self, user_id: UUID, lesson_id: UUID) -> None:
        await self.repo.delete(user_id, lesson_id)
