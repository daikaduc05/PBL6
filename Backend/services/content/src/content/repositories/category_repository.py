from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from content.models.category import Category

class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, category_id: uuid.UUID) -> Optional[Category]:
        return await self._session.get(Category, category_id)

    async def get_by_slug(self, slug: str) -> Optional[Category]:
        result = await self._session.execute(select(Category).where(Category.slug == slug))
        return result.scalars().first()

    async def get_all(self) -> list[Category]:
        result = await self._session.execute(select(Category).order_by(Category.sort_order))
        return list(result.scalars().all())

    async def create(self, name: str, slug: str, parent_id: Optional[uuid.UUID], sort_order: int) -> Category:
        category = Category(name=name, slug=slug, parent_id=parent_id, sort_order=sort_order)
        self._session.add(category)
        await self._session.flush()
        return category

    async def update(self, category: Category, update_data: dict) -> Category:
        for key, value in update_data.items():
            setattr(category, key, value)
        await self._session.flush()
        return category

    async def delete(self, category: Category) -> None:
        await self._session.delete(category)
        await self._session.flush()

    async def get_children(self, parent_id: uuid.UUID) -> list[Category]:
        result = await self._session.execute(select(Category).where(Category.parent_id == parent_id))
        return list(result.scalars().all())
