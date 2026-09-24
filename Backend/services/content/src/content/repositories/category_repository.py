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

    async def get_all(self) -> list[Category]:
        result = await self._session.execute(select(Category))
        return list(result.scalars().all())

    async def create(self, name: str, description: Optional[str] = None) -> Category:
        category = Category(name=name, description=description)
        self._session.add(category)
        await self._session.flush()
        return category
