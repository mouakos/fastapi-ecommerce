"""Schemas for Order operations."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models.order import OrderStatus
from app.schemas.common import UUIDMixin


class OrderCreate(BaseModel):
    """Schema for creating a new order."""

    shipping_address_id: UUID
    billing_address_id: UUID

    model_config = ConfigDict(frozen=True)


class OrderItemRead(BaseModel):
    """Schema for reading order items."""

    product_id: UUID
    quantity: int
    unit_price: Decimal
    product_name: str
    image_url: HttpUrl | None = None

    model_config = ConfigDict(frozen=True)


class OrderRead(UUIDMixin):
    """Schema for reading orders."""

    order_number: str
    total_amount: float
    status: OrderStatus
    items: list[OrderItemRead]

    model_config = ConfigDict(frozen=True)
