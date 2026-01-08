"""Category model with self-referencing parent-child relationships."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Column, DateTime, Field, Relationship

from app.utils.utc_time import utcnow

from .base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.product import Product


class Category(UUIDMixin, TimestampMixin, table=True):
    """Category model for organizing products into hierarchical categories."""

    __tablename__ = "categories"

    name: str = Field(index=True)
    slug: str = Field(unique=True, index=True)
    parent_id: UUID | None = Field(default=None, foreign_key="categories.id")
    description: str | None = None
    image_url: str | None = None
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    # Relationships
    parent: Optional["Category"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Category.id"}
    )
    children: list["Category"] = Relationship(
        back_populates="parent", sa_relationship_kwargs={"lazy": "selectin"}
    )

    products: list["Product"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"lazy": "selectin"},
        cascade_delete=True,
    )
