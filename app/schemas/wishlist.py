"""Schemas for Wishlist operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TwoDecimalBaseModel, UUIDMixin


class AddToWishlistRequest(BaseModel):
    """Schema for adding an item to the wishlist."""

    product_id: UUID

    model_config = ConfigDict(frozen=True)


class WishlistItemPublic(UUIDMixin, TwoDecimalBaseModel):
    """Schema for reading a wishlist item."""

    product_id: UUID
    product_name: str
    product_slug: str
    product_price: Decimal = Field(max_digits=10)
    product_image_url: str | None
    product_in_stock: bool
    product_is_active: bool
    added_at: datetime

    model_config = ConfigDict(frozen=True)


class WishlistStatsResponse(BaseModel):
    """Schema for reading wishlist statistics."""

    count: int

    model_config = ConfigDict(frozen=True)


class WishlistActionResponse(BaseModel):
    """Schema for wishlist action responses."""

    message: str
    product_id: UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Product added to wishlist successfully.",
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )
