"""Pydantic Schemas for Product."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, computed_field

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
                "category_id": None,
                "is_published": True,
            }
        }
    }


class ProductRead(ProductBase, UUIDMixin):
    """Schema for reading a Product."""

    slug: str
    sku: str
    created_at: datetime

    @property
    @computed_field
    def in_stock(self) -> bool:
        """Check if the product is in stock."""
        return self.stock > 0


class ProductUpdate(BaseModel):
    """Schema for updating a Product."""

    name: str = Field(..., max_length=255, min_length=2)
    price: Decimal | None = Field(None, gt=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(None, ge=0)
    description: str | None = None
    image_url: HttpUrl | None = None
    category_id: UUID | None = None
    is_published: bool | None = None
