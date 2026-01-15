"""Schemas for Wishlist operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import UUIDMixin


class WishlistCreate(BaseModel):
    """Schema for adding an item to the wishlist."""

    product_id: UUID

    model_config = ConfigDict(frozen=True)


class WishlistItemRead(UUIDMixin):
    """Schema for reading a wishlist item."""

    product_id: UUID
    product_name: str
    product_slug: str
    product_price: Decimal
    product_image_url: str | None
    product_stock_quantity: int
    product_is_active: bool
    added_at: datetime

    model_config = ConfigDict(frozen=True)


class WishlistRead(BaseModel):
    """Schema for reading wishlist items."""

    items: list[WishlistItemRead]
    total_items: int

    model_config = ConfigDict(frozen=True)


class WishlistStatsRead(BaseModel):
    """Schema for reading wishlist statistics."""

    count: int

    model_config = ConfigDict(frozen=True)


class WishlistActionRead(BaseModel):
    """Schema for reading wishlist action result."""

    message: str
    product_id: UUID | None

    model_config = ConfigDict(frozen=True)
