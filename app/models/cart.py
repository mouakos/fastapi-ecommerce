"""Cart model for storing shopping cart information."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Column
from sqlmodel import DateTime, Field, Relationship, UniqueConstraint

from app.models.base import ModelBase, TimestampMixin
from app.utils.utc_time import utcnow

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Cart(ModelBase, TimestampMixin, table=True):
    """Cart model for storing shopping cart information."""

    __tablename__ = "carts"
    user_id: UUID | None = Field(default=None, foreign_key="users.id", index=True, unique=True)
    session_id: str | None = Field(default=None, index=True, unique=True)
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    # Relationships
    items: list["CartItem"] = Relationship(
        back_populates="cart", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    user: Optional["User"] = Relationship(back_populates="cart")


class CartItem(ModelBase, table=True):
    """Cart item model for storing items in a shopping cart."""

    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="uix_cart_product"),)

    cart_id: UUID = Field(foreign_key="carts.id", index=True, ondelete="CASCADE")
    product_id: UUID = Field(foreign_key="products.id", index=True, ondelete="CASCADE")
    quantity: int
    added_at: datetime = Field(default_factory=utcnow)

    # snapshot fields to preserve product details at the time of addition
    unit_price: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    product_name: str
    product_image_url: str | None = None

    # Relationships
    cart: "Cart" = Relationship(back_populates="items", sa_relationship_kwargs={"lazy": "selectin"})
    product: "Product" = Relationship(
        back_populates="cart_items", sa_relationship_kwargs={"lazy": "selectin"}
    )
