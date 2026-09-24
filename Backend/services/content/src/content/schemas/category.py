from pydantic import BaseModel, Field
import uuid
from typing import Optional

class CategoryBase(BaseModel):
    name: str = Field(..., title="Tên danh mục")
    description: Optional[str] = Field(None, title="Mô tả danh mục")

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
