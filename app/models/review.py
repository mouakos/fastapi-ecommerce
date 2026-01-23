"""Review model for storing product reviews."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Column, Field, Relationship, UniqueConstraint
from sqlmodel import Enum as SQLEnum

from app.models.common import ModelBase, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class ReviewStatus(StrEnum):
    """Enumeration for review statuses."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Review(ModelBase, TimestampMixin, table=True):
    """Review model for storing product reviews."""

    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uix_user_product_review"),)

    user_id: UUID = Field(default=None, foreign_key="users.id", index=True, ondelete="CASCADE")
    product_id: UUID = Field(
        default=None, foreign_key="products.id", index=True, ondelete="CASCADE"
    )
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
    status: ReviewStatus = Field(
        default=ReviewStatus.PENDING,
        sa_column=Column(
            SQLEnum(
                ReviewStatus,
                values_callable=lambda x: [e.value for e in x],
                native_enum=False,
                create_constraint=True,
                length=50,
                validate_strings=True,
                name="review_status",
            ),
            nullable=False,
            index=True,
        ),
    )
    moderated_at: datetime | None = None
    moderated_by: UUID | None = Field(default=None, foreign_key="users.id", index=True)

    # Relationships
    user: "User" = Relationship(
        back_populates="reviews",
        sa_relationship_kwargs={"foreign_keys": "[Review.user_id]"},
    )
    product: "Product" = Relationship(back_populates="reviews")
