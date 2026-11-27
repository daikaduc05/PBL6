import uuid

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(..., title="Tên danh mục")
    slug: str = Field(..., title="Slug danh mục (URL-friendly)")
    parent_id: uuid.UUID | None = Field(None, title="ID danh mục cha")
    sort_order: int = Field(0, title="Thứ tự hiển thị")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, title="Tên danh mục")
    slug: str | None = Field(None, title="Slug danh mục")
    parent_id: uuid.UUID | None = Field(None, title="ID danh mục cha")
    sort_order: int | None = Field(None, title="Thứ tự hiển thị")


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class CategoryTreeResponse(CategoryResponse):
    children: list["CategoryTreeResponse"] = []


CategoryTreeResponse.model_rebuild()
