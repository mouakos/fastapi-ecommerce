"""Pydantic Schemas for Product."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.common import UUIDMixin


class ProductBase(BaseModel):
    """Base schema for Product."""

    name: str = Field(..., max_length=255, min_length=2)
    price: Decimal = Field(Decimal("0.00"), ge=0, max_digits=10, decimal_places=2)
    stock: int = Field(0, ge=0)
    category_id: UUID | None = None
    description: str | None = Field(None, max_length=2000)
    image_url: HttpUrl | None = Field(None, max_length=500)
    is_active: bool = True


class ProductCreate(ProductBase):
    """Schema for creating a Product."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "name": "Sample Product",
                "price": 19.99,
                "stock": 100,
                "category_id": "123e4567-e89b-12d3-a456-426614174000",
                "description": "This is a sample product description.",
                "image_url": "https://example.com/image.png",
                "is_active": True,
            }
        },
    )


class ProductRead(ProductBase, UUIDMixin):
    """Schema for reading a Product."""

    slug: str
    sku: str
    created_at: datetime

    model_config = ConfigDict(frozen=True)


class ProductDetailRead(ProductRead, UUIDMixin):
    """Schema for reading a Product."""

    average_rating: float | None = Field(
        None, ge=1, le=5, description="Average rating from reviews (1-5)"
    )
    review_count: int = Field(0, ge=0, description="Total number of reviews")
    in_stock: bool

    model_config = ConfigDict(frozen=True)


class ProductUpdate(BaseModel):
    """Schema for updating a Product."""

    name: str | None = Field(None, max_length=255, min_length=2)
    price: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(None, ge=0)
    description: str | None = Field(None, max_length=2000)
    image_url: HttpUrl | None = Field(None, max_length=500)
    category_id: UUID | None = None
    is_active: bool | None = None

    model_config = ConfigDict(frozen=True)
