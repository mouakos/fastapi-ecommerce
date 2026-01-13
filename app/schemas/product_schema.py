"""Pydantic Schemas for Product."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.base import UUIDMixin


class ProductBase(BaseModel):
    """Base schema for Product."""

    name: str = Field(..., max_length=255, min_length=2)
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(0, ge=0)
    category_id: UUID | None = None
    description: str | None = None
    image_url: HttpUrl | None = None
    is_published: bool = True


class ProductCreate(ProductBase):
    """Schema for creating a Product."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Smartphone",
                "description": "A high-end smartphone with a great camera.",
                "price": 699.99,
                "stock": 50,
                "image_url": "https://example.com/smartphone.jpg",
                "category_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_published": True,
            }
        }
    }


class ProductRead(ProductBase, UUIDMixin):
    """Schema for reading a Product."""

    slug: str
    sku: str
    created_at: datetime


class ProductDetailRead(ProductRead, UUIDMixin):
    """Schema for reading a Product."""

    average_rating: float | None = Field(
        None, ge=1, le=5, description="Average rating from reviews (1-5)"
    )
    review_count: int = Field(default=1, ge=0, description="Total number of reviews")
    in_stock: bool


class ProductUpdate(BaseModel):
    """Schema for updating a Product."""

    name: str = Field(..., max_length=255, min_length=2)
    price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(None, ge=0)
    description: str | None = None
    image_url: HttpUrl | None = None
    category_id: UUID | None = None
    is_published: bool | None = None
