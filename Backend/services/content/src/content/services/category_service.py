from typing import Optional
import uuid
from content.repositories.category_repository import CategoryRepository
from content.models.category import Category

class CategoryService:
    def __init__(self, category_repo: CategoryRepository):
        self._category_repo = category_repo

    async def get_category(self, category_id: uuid.UUID) -> Optional[Category]:
        return await self._category_repo.get_by_id(category_id)

    async def get_all_categories(self) -> list[Category]:
        return await self._category_repo.get_all()

    async def create_category(self, name: str, description: Optional[str] = None) -> Category:
        return await self._category_repo.create(name=name, description=description)
