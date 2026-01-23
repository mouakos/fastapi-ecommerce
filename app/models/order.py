"""Order model for storing order information."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, Relationship

from app.models.address import AddressBase
from app.models.common import ModelBase, TimestampMixin

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.product import Product
    from app.models.user import User


class OrderAddressKind(StrEnum):
    """Order address type."""

    SHIPPING = "shipping"
    BILLING = "billing"


class OrderStatus(StrEnum):
    """Enumeration for order statuses."""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"


class Order(ModelBase, TimestampMixin, table=True):
    """Order model for storing order information."""

    __tablename__ = "orders"
    user_id: UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        sa_column=Column(
            SQLEnum(
                OrderStatus,
                values_callable=lambda x: [e.value for e in x],
                native_enum=False,
                create_constraint=True,
                length=50,
                validate_strings=True,
                name="order_status",
            ),
            nullable=False,
            index=True,
        ),
    )
    total_amount: Decimal = Field(Decimal("0.00"), max_digits=10, decimal_places=2)
    order_number: str = Field(index=True, unique=True, max_length=50)
    shipped_at: datetime | None = Field(default=None)
    paid_at: datetime | None = Field(default=None)
    canceled_at: datetime | None = Field(default=None)
    delivered_at: datetime | None = Field(default=None)

    # Relationships
    user: "User" = Relationship(
        back_populates="orders", sa_relationship_kwargs={"lazy": "selectin"}
    )
    items: list["OrderItem"] = Relationship(
        back_populates="order", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    addresses: list["OrderAddress"] = Relationship(
        back_populates="order", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    payments: list["Payment"] = Relationship(
        back_populates="order", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )


class OrderItem(ModelBase, table=True):
    """OrderItem model for storing order item information."""

    __tablename__ = "order_items"
    __table_args__ = (UniqueConstraint("order_id", "product_id", name="uix_order_product"),)

    order_id: UUID = Field(foreign_key="orders.id", index=True, ondelete="CASCADE")
    product_id: UUID = Field(foreign_key="products.id", index=True, ondelete="CASCADE")
    quantity: int = Field(1, ge=1)

    # Snapshot of product details at the time of order
    unit_price: Decimal = Field(Decimal("0.00"), max_digits=10, decimal_places=2)
    product_name: str = Field(max_length=255)
    product_image_url: str | None = Field(default=None, max_length=500)

    # Relationships
    order: "Order" = Relationship(
        back_populates="items", sa_relationship_kwargs={"lazy": "selectin"}
    )
    product: "Product" = Relationship(
        back_populates="order_items", sa_relationship_kwargs={"lazy": "selectin"}
    )


class OrderAddress(AddressBase, table=True):
    """Snapshot of an address used for an order."""

    __tablename__ = "order_addresses"
    __table_args__ = (UniqueConstraint("order_id", "kind", name="uix_order_address_kind"),)

    order_id: UUID = Field(foreign_key="orders.id", index=True, ondelete="CASCADE")
    kind: OrderAddressKind = Field(
        sa_column=Column(
            SQLEnum(
                OrderAddressKind,
                values_callable=lambda x: [e.value for e in x],
                native_enum=False,
                create_constraint=True,
                length=20,
                validate_strings=True,
                name="order_address_kind",
            ),
            nullable=False,
            index=True,
        ),
    )

    order: Order = Relationship(
        back_populates="addresses", sa_relationship_kwargs={"lazy": "selectin"}
    )
