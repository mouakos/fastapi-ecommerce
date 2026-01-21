"""Schemas for payment processing."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentIntentRequest(BaseModel):
    """Schema for creating a payment intent."""

    order_id: UUID

    model_config = ConfigDict(frozen=True)


class PaymentIntentResponse(BaseModel):
    """Schema for payment intent response."""

    client_secret: str
    intent_id: str
    amount: Decimal = Field(decimal_places=2, max_digits=10)
    currency: str

    model_config = ConfigDict(frozen=True)
