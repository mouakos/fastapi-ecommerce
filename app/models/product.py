"""Product model definitions for the ecommerce API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from roman_numerals import TYPE_CHECKING
from sqlmodel import Column, DateTime, Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin
from app.models.category import Category
from app.utils.utc_time import utcnow

if TYPE_CHECKING:
    from app.models.category import Category


class Product(UUIDMixin, TimestampMixin, table=True):
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
    category_id: UUID = Field(foreign_key="categories.id", ondelete="CASCADE", index=True)
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    # Relationships
    category: "Category" = Relationship(back_populates="products")
