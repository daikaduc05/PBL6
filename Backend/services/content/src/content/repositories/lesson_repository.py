import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from content.models.lesson import Lesson


class LessonRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, lesson_id: uuid.UUID) -> Lesson | None:
        return await self._session.get(Lesson, lesson_id)

    async def get_all(
        self,
        category_id: uuid.UUID | None = None,
        level: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Lesson]:
        query = select(Lesson)
        if category_id:
            query = query.where(Lesson.category_id == category_id)
        if level:
            query = query.where(Lesson.level == level)

        query = query.order_by(Lesson.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> Lesson:
        lesson = Lesson(**kwargs)
        self._session.add(lesson)
        await self._session.flush()
        return lesson

    async def update(self, lesson: Lesson, update_data: dict[str, Any]) -> Lesson:
        for key, value in update_data.items():
            setattr(lesson, key, value)
        await self._session.flush()
        return lesson

    async def delete(self, lesson: Lesson) -> None:
        await self._session.delete(lesson)
        await self._session.flush()
