"""Pydantic Schemas for Product."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, computed_field

from app.schemas.common import TwoDecimalBaseModel, UUIDMixin


class ProductBase(BaseModel):
    """Base schema for Product."""

    name: str = Field(..., max_length=255, min_length=2)
    price: Decimal = Field(Decimal("0.00"), ge=0, max_digits=10, decimal_places=2)
    stock: int = Field(0, ge=0)
    category_id: UUID | None = None
    description: str | None = Field(None, max_length=2000)
    image_url: HttpUrl | None = Field(None, max_length=500)
    is_active: bool = True
    discount_percentage: int = Field(0, ge=0, le=100)


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
                "discount_percentage": 10,
            }
        },
    )


class ProductUpdate(BaseModel):
    """Schema for updating a Product."""

    name: str | None = Field(None, max_length=255, min_length=2)
    price: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(None, ge=0)
    description: str | None = Field(None, max_length=2000)
    image_url: HttpUrl | None = Field(None, max_length=500)
    category_id: UUID | None = None
    is_active: bool | None = None
    discount_percentage: int | None = Field(None, ge=0, le=100)
    model_config = ConfigDict(frozen=True)


class ProductPublic(ProductBase, UUIDMixin, TwoDecimalBaseModel):
    """Schema for reading a Product."""

    slug: str = Field(..., max_length=100)
    sku: str = Field(..., max_length=100)
    created_at: datetime

    model_config = ConfigDict(frozen=True)


class ProductAdmin(ProductPublic):
    """Schema for reading a Product in admin context."""

    updated_at: datetime

    model_config = ConfigDict(frozen=True)


class ProductDetail(ProductPublic):
    """Schema for reading a Product."""

    average_rating: float | None = Field(
        None, ge=1, le=5, description="Average rating from reviews (1-5)"
    )
    review_count: int = Field(0, ge=0, description="Total number of reviews")

    @property
    @computed_field
    def in_stock(self) -> bool:
        """Determine if the product is in stock."""
        return self.stock > 0

    model_config = ConfigDict(frozen=True)


class ProductAutocompleteResponse(BaseModel):
    """Schema for product name autocomplete suggestions."""

    suggestions: list[str] = Field(..., description="List of product name suggestions (max 10)")

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "suggestions": [
                        "iPhone 16 Pro",
                        "iPhone 16",
                        "iPhone 15 Pro Max",
                        "iPhone 14",
                    ]
                }
            ]
        },
    )


class ProductAvailabilityFilter(StrEnum):
    """Filters for product availability."""

    ALL = "all"
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"


class ProductSortByField(StrEnum):
    """Fields to sort products by."""

    NAME = "name"
    PRICE = "price"
    RATING = "rating"
    POPULARITY = "popularity"
    CREATED_AT = "created_at"
