"""Payment model for storing payment information."""

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum as SQLEnum
from sqlmodel import Column, Field, Relationship

from app.models.common import ModelBase, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class PaymentStatus(StrEnum):
    """Enumeration for payment statuses."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class PaymentMethod(StrEnum):
    """Enumeration for payment methods."""

    CARD = "card"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    BANK_TRANSFER = "bank_transfer"


class Currency(StrEnum):
    """Enumeration for currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class Payment(ModelBase, TimestampMixin, table=True):
    """Payment model for storing payment information."""

    __tablename__ = "payments"
    order_id: UUID = Field(default=None, foreign_key="orders.id", index=True, ondelete="CASCADE")
    amount: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    session_id: str = Field(index=True, unique=True, max_length=100)
    currency: Currency = Field(
        default=Currency.USD,
        sa_column=Column(
            SQLEnum(
                Currency,
                values_callable=lambda x: [e.value for e in x],
                native_enum=False,
                create_constraint=True,
                length=50,
                validate_strings=True,
                name="currency",
            ),
            nullable=False,
        ),
    )
    payment_method: PaymentMethod = Field(
        default=PaymentMethod.CARD,
        sa_column=Column(
            SQLEnum(
                PaymentMethod,
                values_callable=lambda x: [e.value for e in x],
                native_enum=False,
                create_constraint=True,
                length=50,
                validate_strings=True,
                name="payment_method",
            ),
            nullable=False,
            index=True,
        ),
    )
    status: PaymentStatus = Field(
        default=PaymentStatus.PENDING,
        sa_column=Column(
            SQLEnum(
                PaymentStatus,
                values_callable=lambda x: [e.value for e in x],
                native_enum=False,
                create_constraint=True,
                length=50,
                validate_strings=True,
                name="payment_status",
            ),
            nullable=False,
            index=True,
        ),
    )

    # Relationships
    order: "Order" = Relationship(
        back_populates="payments", sa_relationship_kwargs={"lazy": "selectin"}
    )
