from datetime import UTC, datetime
from uuid import UUID

from learning.models.history import History
from sqlalchemy import desc, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession


class HistoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_and_lesson(self, user_id: UUID, lesson_id: UUID) -> History | None:
        query = select(History).where(
            History.user_id == user_id,
            History.lesson_id == lesson_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def upsert(self, user_id: UUID, lesson_id: UUID, score: float) -> History:
        now = datetime.now(UTC)
        stmt = (
            insert(History)
            .values(
                user_id=user_id,
                lesson_id=lesson_id,
                highest_score=score,
                completed_at=now,
            )
            .on_conflict_do_update(
                constraint="histories_user_lesson_key",
                set_={
                    "highest_score": func.greatest(History.highest_score, score),
                    "completed_at": now,
                },
            )
            .returning(History)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()

    async def list_by_user(self, user_id: UUID) -> list[History]:
        query = (
            select(History).where(History.user_id == user_id).order_by(desc(History.completed_at))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_last_activity_for_user(self, user_id: UUID) -> History | None:
        query = (
            select(History)
            .where(History.user_id == user_id)
            .order_by(desc(History.completed_at))
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_last_activities(
        self, since: datetime | None = None, limit: int = 1000
    ) -> list[History]:
        query = (
            select(History)
            .distinct(History.user_id)
            .order_by(History.user_id, desc(History.completed_at))
        )
        if since is not None:
            query = query.where(History.completed_at >= since)
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
