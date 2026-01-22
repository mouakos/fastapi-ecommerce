"""Schemas for Order operations."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.order import OrderStatus
from app.schemas.common import UUIDMixin


class OrderCreate(BaseModel):
    """Schema for creating a new order."""

    shipping_address_id: UUID
    billing_address_id: UUID

    model_config = ConfigDict(frozen=True)


class OrderItemPublic(BaseModel):
    """Schema for reading order items."""

    product_id: UUID
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., max_digits=10, decimal_places=2)
    product_name: str = Field(..., max_length=255)
    image_url: HttpUrl | None = Field(..., max_length=500)

    model_config = ConfigDict(frozen=True)


class OrderPublic(UUIDMixin):
    """Schema for reading orders."""

    order_number: str = Field(..., description="Unique order number", max_length=100)
    total_amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    status: OrderStatus
    items: list[OrderItemPublic]
    created_at: datetime

    model_config = ConfigDict(frozen=True)


class OrderAdmin(UUIDMixin):
    """Schema for reading order information in admin context."""

    user_id: UUID
    user_email: str = Field(
        ..., description="Email of the user who placed the order", max_length=255
    )
    order_number: str = Field(..., description="Unique order number", max_length=100)
    total_amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    shipped_at: datetime | None
    paid_at: datetime | None
    canceled_at: datetime | None
    delivered_at: datetime | None

    model_config = ConfigDict(frozen=True)


class OrderStatusUpdateRequest(BaseModel):
    """Schema for updating an order's status."""

    status: OrderStatus = Field(
        ...,
        description="New status: 'pending', 'paid', 'shipped', 'delivered', 'cancelled'",
    )

    model_config = ConfigDict(frozen=True)


class OrderSortByField(StrEnum):
    """Fields to sort orders by."""

    TOTAL_AMOUNT = "total_amount"
    STATUS = "status"
    CREATED_AT = "created_at"


class OrderActionResponse(BaseModel):
    """Schema for order action responses."""

    message: str
    order_id: UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Order status updated successfully.",
                "order_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )
