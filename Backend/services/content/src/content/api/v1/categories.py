import uuid

from fastapi import APIRouter, Depends, status
from pbl6_common.deps import require_role
from pbl6_common.errors import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

from content.deps import get_db
from content.repositories.category_repository import CategoryRepository
from content.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryTreeResponse,
    CategoryUpdate,
)
from content.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


def get_category_service(session: AsyncSession = Depends(get_db)) -> CategoryService:
    repo = CategoryRepository(session)
    return CategoryService(repo)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("ADMIN", "EDITOR"))],
)
async def create_category(
    data: CategoryCreate, service: CategoryService = Depends(get_category_service)
):
    category = await service.create_category(data)
    return category


@router.get("", response_model=list[CategoryTreeResponse])
async def get_categories(
    q: str | None = None, service: CategoryService = Depends(get_category_service)
):
    categories = await service.get_category_tree(q=q)
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID, service: CategoryService = Depends(get_category_service)
):
    category = await service.get_category(category_id)
    if not category:
        raise NotFoundError("Không tìm thấy danh mục.")
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_role("ADMIN", "EDITOR"))],
)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
):
    category = await service.update_category(category_id, data)
    return category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("ADMIN", "EDITOR"))],
)
async def delete_category(
    category_id: uuid.UUID, service: CategoryService = Depends(get_category_service)
):
    await service.delete_category(category_id)
