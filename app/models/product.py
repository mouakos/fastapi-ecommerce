"""Product model for storing product information."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.base import ModelBase, TimestampMixin
from app.models.category import Category

if TYPE_CHECKING:
    from app.models.cart import CartItem
    from app.models.category import Category


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
    category: Optional["Category"] = Relationship(back_populates="products")

    cart_items: list["CartItem"] = Relationship(
        back_populates="product", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
