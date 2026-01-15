"""Schemas for category operations."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.common import UUIDMixin


class CategoryBase(BaseModel):
    """Schema for creating a new category."""

    name: str = Field(..., min_length=2, max_length=50)
    parent_id: UUID | None = None
    description: str | None = Field(None, max_length=1000)
    image_url: HttpUrl | None = Field(None, max_length=255)

    model_config = ConfigDict(frozen=True)


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "name": "Electronics",
                "parent_id": None,
                "description": "Category for electronic products",
                "image_url": "https://example.com/images/electronics.png",
            }
        },
    )


class CategoryRead(CategoryBase, UUIDMixin):
    """Schema for reading category information."""

    slug: str

    model_config = ConfigDict(frozen=True)


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""

    name: str | None = Field(None, min_length=1, max_length=50)
    parent_id: UUID | None = None
    description: str | None = None
    image_url: HttpUrl | None = Field(None, max_length=255)

    model_config = ConfigDict(frozen=True)
