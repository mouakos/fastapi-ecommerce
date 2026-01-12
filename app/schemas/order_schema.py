"""Schemas for Order operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, HttpUrl

from app.models.order import OrderStatus
from app.schemas.base import UUIDMixin


class OrderCreate(BaseModel):
    """Schema for creating a new order."""

    shipping_address_id: UUID
    billing_address_id: UUID


class OrderItemRead(BaseModel):
    """Schema for reading order items."""

    product_id: UUID
    quantity: int
    unit_price: Decimal
    product_name: str
    order_at: datetime
    image_url: HttpUrl | None = None


class OrderRead(UUIDMixin):
    """Schema for reading orders."""

    order_number: str
    total_amount: float
    status: OrderStatus
    items: list[OrderItemRead]
