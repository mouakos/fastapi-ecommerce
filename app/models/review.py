"""Review model for storing product reviews."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.base import ModelBase, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Review(ModelBase, TimestampMixin, table=True):
    """Review model for storing product reviews."""

    __tablename__ = "reviews"
    user_id: UUID = Field(default=None, foreign_key="users.id", index=True, ondelete="CASCADE")
    product_id: UUID = Field(
        default=None, foreign_key="products.id", index=True, ondelete="CASCADE"
    )
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
    is_approved: bool = Field(default=False)
    approved_at: datetime | None = Field(default=None)
    approved_by: UUID | None = Field(default=None, foreign_key="users.id", index=True)

    # Relationships
    user: "User" = Relationship(
        back_populates="reviews",
        sa_relationship_kwargs={"lazy": "selectin", "foreign_keys": "[Review.user_id]"},
    )
    product: "Product" = Relationship(
        back_populates="reviews", sa_relationship_kwargs={"lazy": "selectin"}
    )
