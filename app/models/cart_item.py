"""Cart item model for storing items in a shopping cart."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, UniqueConstraint

from app.models.base import ModelBase
from app.utils.utc_time import utcnow

if TYPE_CHECKING:
    from app.models.cart import Cart
    from app.models.product import Product


class CartItem(ModelBase, table=True):
    """Cart item model for storing items in a shopping cart."""

    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id", name="uix_cart_product"),)

    cart_id: UUID = Field(foreign_key="carts.id", index=True, ondelete="CASCADE")
    product_id: UUID = Field(foreign_key="products.id", index=True, ondelete="CASCADE")
    quantity: int
    added_at: datetime = Field(default_factory=utcnow)

    # snapshot fields to preserve product details at the time of addition
    unit_price: Decimal
    product_name: str
    product_image_url: str | None = None

    # Relationships
    cart: "Cart" = Relationship(back_populates="items")
    product: "Product" = Relationship(back_populates="cart_items")
