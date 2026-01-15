"""Schemas for payment processing."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.payment import Currency


class PaymentCheckoutSessionCreate(BaseModel):
    """Schema for creating a payment intent."""

    order_id: UUID

    model_config = ConfigDict(frozen=True)


class PaymentCheckoutSessionRead(BaseModel):
    """Schema for reading payment checkout session details."""

    checkout_url: str
    session_id: str
    amount: Decimal
    currency: Currency
    expires_at: datetime
    order_id: UUID

    model_config = ConfigDict(frozen=True)
