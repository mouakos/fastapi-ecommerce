"""Cart model for storing shopping cart information."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Column
from sqlmodel import DateTime, Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin
from app.utils.utc_time import utcnow

if TYPE_CHECKING:
    from app.models.cart_item import CartItem
    from app.models.user import User


class Cart(UUIDMixin, TimestampMixin, table=True):
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
