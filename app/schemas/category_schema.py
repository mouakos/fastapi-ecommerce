"""Schemas for category operations in the ecommerce API."""

from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.base import UUIDMixin


class CategoryBase(BaseModel):
    """Schema for creating a new category."""

    name: str = Field(..., min_length=1, max_length=255)
    parent_id: UUID | None = None
    description: str | None = None
    image_url: HttpUrl | None = None


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Electronics",
                "parent_id": "123e4567-e89b-12d3-a456-426614174000",
                "description": "Electronic devices and accessories",
                "image_url": "https://example.com/electronics.jpg",
            }
        }
    }


class CategoryRead(CategoryBase, UUIDMixin):
    """Schema for reading category information."""

    slug: str


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""

    name: str | None = Field(None, min_length=1, max_length=255)
    parent_id: UUID | None = None
    description: str | None = None
    image_url: HttpUrl | None = None
