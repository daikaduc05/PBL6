from fastapi import APIRouter, Depends, HTTPException
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from content.deps import get_db
from content.schemas.category import CategoryCreate, CategoryResponse
from content.repositories.category_repository import CategoryRepository
from content.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])

def get_category_service(session: AsyncSession = Depends(get_db)) -> CategoryService:
    repo = CategoryRepository(session)
    return CategoryService(repo)

@router.post("", response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate, 
    service: CategoryService = Depends(get_category_service)
):
    category = await service.create_category(name=data.name, description=data.description)
    return category

@router.get("", response_model=list[CategoryResponse])
async def get_categories(
    service: CategoryService = Depends(get_category_service)
):
    categories = await service.get_all_categories()
    return categories

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    service: CategoryService = Depends(get_category_service)
):
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category
