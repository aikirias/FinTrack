from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.models.category import CategoryType


class CategoryBase(BaseModel):
    name: str = Field(max_length=100)
    type: CategoryType
    parent_id: int | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    type: CategoryType | None = None
    parent_id: int | None = Field(default=None)
    is_archived: bool | None = None


class CategoryOut(CategoryBase):
    id: int
    is_default: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    children: List["CategoryOut"] = Field(default_factory=list)

    class Config:
        from_attributes = True


CategoryOut.model_rebuild()
