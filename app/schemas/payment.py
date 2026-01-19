"""Schemas for payment processing."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CheckoutRequest(BaseModel):
    """Schema for creating a payment checkout session."""

    order_id: UUID

    model_config = ConfigDict(frozen=True)


class CheckoutResponse(BaseModel):
    """Schema for checkout session response."""

    checkout_url: str

    model_config = ConfigDict(frozen=True)
