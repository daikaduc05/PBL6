from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from learning.models.favorite import FavoriteLesson
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession


class FavoriteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_lesson(self, user_id: UUID, lesson_id: UUID) -> FavoriteLesson | None:
        query = select(FavoriteLesson).where(
            FavoriteLesson.user_id == user_id,
            FavoriteLesson.lesson_id == lesson_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[FavoriteLesson]:
        query = (
            select(FavoriteLesson)
            .where(FavoriteLesson.user_id == user_id)
            .order_by(desc(FavoriteLesson.created_at))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add(self, user_id: UUID, lesson_id: UUID) -> FavoriteLesson:
        fav = await self.get_by_user_and_lesson(user_id, lesson_id)
        if fav:
            return fav
        fav = FavoriteLesson(
            user_id=user_id,
            lesson_id=lesson_id,
            created_at=datetime.now(UTC),
        )
        self.db.add(fav)
        await self.db.commit()
        await self.db.refresh(fav)
        return fav

    async def delete(self, user_id: UUID, lesson_id: UUID) -> bool:
        fav = await self.get_by_user_and_lesson(user_id, lesson_id)
        if not fav:
            return False
        await self.db.delete(fav)
        await self.db.commit()
        return True
