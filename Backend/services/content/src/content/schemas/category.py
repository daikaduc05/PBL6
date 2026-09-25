from pydantic import BaseModel, Field
import uuid
from typing import Optional, List

class CategoryBase(BaseModel):
    name: str = Field(..., title="Tên danh mục")
    slug: str = Field(..., title="Slug danh mục (URL-friendly)")
    parent_id: Optional[uuid.UUID] = Field(None, title="ID danh mục cha")
    sort_order: int = Field(0, title="Thứ tự hiển thị")

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, title="Tên danh mục")
    slug: Optional[str] = Field(None, title="Slug danh mục")
    parent_id: Optional[uuid.UUID] = Field(None, title="ID danh mục cha")
    sort_order: Optional[int] = Field(None, title="Thứ tự hiển thị")

class CategoryResponse(CategoryBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

class CategoryTreeResponse(CategoryResponse):
    children: List["CategoryTreeResponse"] = []

CategoryTreeResponse.model_rebuild()
