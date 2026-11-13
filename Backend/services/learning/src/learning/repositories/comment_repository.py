from __future__ import annotations

from uuid import UUID

from learning.models.comment import Comment
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, comment_id: UUID) -> Comment | None:
        query = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_lesson(self, lesson_id: UUID) -> list[Comment]:
        query = (
            select(Comment).where(Comment.lesson_id == lesson_id).order_by(Comment.created_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, comment: Comment) -> Comment:
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def delete(self, comment: Comment) -> None:
        await self.db.delete(comment)
        await self.db.commit()
