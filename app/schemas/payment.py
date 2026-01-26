"""Schemas for payment processing."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentIntentRequest(BaseModel):
    """Schema for creating a payment intent."""

    order_id: UUID

    model_config = ConfigDict(frozen=True)


class PaymentIntentResponse(BaseModel):
    """Schema for payment intent response."""

    client_secret: str = Field(..., description="The client secret needed to complete the payment.")

    model_config = ConfigDict(frozen=True)
