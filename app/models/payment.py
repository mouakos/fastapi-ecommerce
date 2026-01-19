"""Payment model for storing payment information."""

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Column, Field, Relationship
from sqlmodel import Enum as SQLEnum

from app.models.common import ModelBase, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class PaymentStatus(StrEnum):
    """Enumeration for payment statuses."""

    PENDING = "pending"
    SUCCESS = "success"


class Payment(ModelBase, TimestampMixin, table=True):
    """Payment model for storing payment information."""

    __tablename__ = "payments"
    order_id: UUID = Field(default=None, foreign_key="orders.id", index=True, ondelete="CASCADE")
    amount: Decimal = Field(default=Decimal("0.00"), max_digits=10, decimal_places=2)
    currency: str = Field(max_length=50, default="usd", index=True)
    payment_method: str = Field(max_length=50, default="card", index=True)
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
    session_id: str = Field(index=True, unique=True, max_length=100)
    payment_intent_id: str | None = Field(default=None, max_length=100)

    # Relationships
    order: "Order" = Relationship(
        back_populates="payments", sa_relationship_kwargs={"lazy": "selectin"}
    )
