"""Schemas for Wishlist operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base import UUIDMixin


class WishlistCreate(BaseModel):
    """Schema for adding an item to the wishlist."""

    product_id: UUID


class WishlistItemRead(UUIDMixin):
    """Schema for reading a wishlist item."""

    product_id: UUID
    product_name: str
    product_slug: str
    product_price: Decimal
    product_image_url: str | None = None
    product_stock_quantity: int
    product_is_published: bool
    added_at: datetime


class WishlistRead(BaseModel):
    """Schema for reading wishlist items."""

    items: list[WishlistItemRead]
    total_items: int


class WishlistStatsRead(BaseModel):
    """Schema for reading wishlist statistics."""

    count: int


class WishlistActionRead(BaseModel):
    """Schema for reading wishlist action result."""

    message: str
    product_id: UUID | None = None
