"""Product model for storing product information."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.category import Category
from app.models.common import ModelBase, TimestampMixin

if TYPE_CHECKING:
    from app.models.cart import CartItem
    from app.models.category import Category
    from app.models.order import OrderItem
    from app.models.review import Review
    from app.models.wishlist_item import WishlistItem


class Product(ModelBase, TimestampMixin, table=True):
    """Product model for storing product information."""

    __tablename__ = "products"

    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    description: str | None = None
    price: Decimal
    stock: int
    sku: str = Field(unique=True, index=True)
    image_url: str | None = None
    is_published: bool = Field(default=True)
    category_id: UUID | None = Field(
        default=None, foreign_key="categories.id", ondelete="CASCADE", index=True
    )

    # Relationships
    category: Optional["Category"] = Relationship(
        back_populates="products", sa_relationship_kwargs={"lazy": "selectin"}
    )

    cart_items: list["CartItem"] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    order_items: list["OrderItem"] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    wishlist_items: list["WishlistItem"] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    reviews: list["Review"] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
