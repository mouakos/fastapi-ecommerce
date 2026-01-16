"""Schemas for Order operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
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
    image_url: HttpUrl | None

    model_config = ConfigDict(frozen=True)


class OrderRead(UUIDMixin):
    """Schema for reading orders."""

    order_number: str
    total_amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    status: OrderStatus
    items: list[OrderItemRead]

    model_config = ConfigDict(frozen=True)


class OrderAdminRead(UUIDMixin):
    """Schema for reading order information in admin context."""

    order_number: str
    user_id: UUID
    user_email: str = Field(..., description="Email of the user who placed the order")
    total_amount: Decimal
    status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    shipped_at: datetime | None
    paid_at: datetime | None
    canceled_at: datetime | None
    delivered_at: datetime | None

    model_config = ConfigDict(frozen=True)


class OrderAdminStatusUpdate(BaseModel):
    """Schema for updating an order's status."""

    status: OrderStatus = Field(
        ...,
        description="New status: 'pending', 'paid', 'shipped', 'delivered', 'cancelled'",
    )

    model_config = ConfigDict(frozen=True)
