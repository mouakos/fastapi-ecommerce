"""Wishlist model for storing user wishlist items."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, UniqueConstraint

from app.models.common import ModelBase
from app.utils.utc_time import utcnow

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class WishlistItem(ModelBase, table=True):
    """Wishlist model for storing user wishlist items."""

    __tablename__ = "wishlist_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uix_user_product"),)

    user_id: UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    product_id: UUID = Field(foreign_key="products.id", index=True, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=utcnow)

    # Relationships
    user: "User" = Relationship(
        back_populates="wishlist_items", sa_relationship_kwargs={"lazy": "selectin"}
    )
    product: "Product" = Relationship(
        back_populates="wishlist_items", sa_relationship_kwargs={"lazy": "selectin"}
    )
