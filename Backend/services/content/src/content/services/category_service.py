import uuid

from content.models.category import Category
from content.repositories.category_repository import CategoryRepository
from content.schemas.category import (
    CategoryCreate,
    CategoryTreeResponse,
    CategoryUpdate,
)
from fastapi import HTTPException


class CategoryService:
    def __init__(self, category_repo: CategoryRepository):
        self._category_repo = category_repo

    async def get_category(self, category_id: uuid.UUID) -> Category | None:
        return await self._category_repo.get_by_id(category_id)

    def _build_tree(self, categories: list[Category]) -> list[CategoryTreeResponse]:
        category_map = {cat.id: CategoryTreeResponse.model_validate(cat) for cat in categories}

        tree = []
        for cat in categories:
            node = category_map[cat.id]
            if cat.parent_id and cat.parent_id in category_map:
                category_map[cat.parent_id].children.append(node)
            else:
                tree.append(node)

        return tree

    async def get_category_tree(self) -> list[CategoryTreeResponse]:
        categories = await self._category_repo.get_all()
        return self._build_tree(categories)

    async def create_category(self, data: CategoryCreate) -> Category:
        existing_slug = await self._category_repo.get_by_slug(data.slug)
        if existing_slug:
            raise HTTPException(
                status_code=400, detail="Slug này đã được sử dụng. Vui lòng chọn slug khác."
            )

        if data.parent_id:
            parent = await self._category_repo.get_by_id(data.parent_id)
            if not parent:
                raise HTTPException(status_code=400, detail="Danh mục cha không tồn tại.")

        return await self._category_repo.create(
            name=data.name, slug=data.slug, parent_id=data.parent_id, sort_order=data.sort_order
        )

    async def update_category(self, category_id: uuid.UUID, data: CategoryUpdate) -> Category:
        category = await self._category_repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục.")

        if data.slug and data.slug != category.slug:
            existing_slug = await self._category_repo.get_by_slug(data.slug)
            if existing_slug:
                raise HTTPException(
                    status_code=400, detail="Slug này đã được sử dụng. Vui lòng chọn slug khác."
                )

        if data.parent_id:
            if data.parent_id == category_id:
                raise HTTPException(
                    status_code=400, detail="Một danh mục không thể làm cha của chính nó."
                )
            parent = await self._category_repo.get_by_id(data.parent_id)
            if not parent:
                raise HTTPException(status_code=400, detail="Danh mục cha không tồn tại.")

        update_data = data.model_dump(exclude_unset=True)
        return await self._category_repo.update(category, update_data)

    async def delete_category(self, category_id: uuid.UUID) -> None:
        category = await self._category_repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Không tìm thấy danh mục.")

        children = await self._category_repo.get_children(category_id)
        if children:
            raise HTTPException(
                status_code=400, detail="Không thể xóa vì danh mục này đang chứa các danh mục con."
            )

        await self._category_repo.delete(category)
