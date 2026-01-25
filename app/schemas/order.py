"""Schemas for Order operations."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.order import OrderAddressKind, OrderStatus
from app.schemas.common import TwoDecimalBaseModel, UUIDMixin


class OrderCreate(BaseModel):
    """Schema for creating a new order."""

    shipping_address_id: UUID
    billing_address_id: UUID

    model_config = ConfigDict(frozen=True)


class OrderItemPublic(TwoDecimalBaseModel):
    """Schema for reading order items."""

    product_id: UUID
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., max_digits=10)
    product_name: str = Field(..., max_length=255)
    product_image_url: HttpUrl | None = Field(..., max_length=500)

    model_config = ConfigDict(frozen=True)


class OrderPublic(UUIDMixin, TwoDecimalBaseModel):
    """Schema for reading orders."""

    user_id: UUID
    order_number: str
    total_amount: Decimal = Field(..., max_digits=10)
    status: OrderStatus
    items: list[OrderItemPublic]
    created_at: datetime
    shipped_at: datetime | None
    paid_at: datetime | None
    canceled_at: datetime | None
    delivered_at: datetime | None
    tax_amount: Decimal
    shipping_amount: Decimal

    model_config = ConfigDict(frozen=True)


class OrderAddressPublic(BaseModel):
    """Schema for reading order address information."""

    full_name: str
    company: str | None
    line1: str
    line2: str | None
    city: str
    state: str | None
    postal_code: str
    country: str
    phone_number: str | None
    kind: OrderAddressKind

    model_config = ConfigDict(frozen=True)


class OrderDetail(OrderPublic):
    """Schema for reading detailed order information."""

    addresses: list[OrderAddressPublic]

    model_config = ConfigDict(frozen=True)


class OrderSortByField(StrEnum):
    """Fields to sort orders by."""

    TOTAL_AMOUNT = "total_amount"
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
