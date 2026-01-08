"""Address model for storing user address information."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Column, DateTime, Field, Relationship

from app.models.base import TimestampMixin, UUIDMixin
from app.utils.utc_time import utcnow

if TYPE_CHECKING:
    from app.models.user import User


class Address(UUIDMixin, TimestampMixin, table=True):
    """Address model for storing user address information."""

    __tablename__ = "addresses"
    user_id: UUID = Field(index=True, foreign_key="users.id", ondelete="CASCADE")
    full_name: str
    company: str | None = None
    line1: str
    line2: str | None = None
    city: str
    state: str | None = None
    postal_code: str
    country: str
    phone_number: str | None = None
    is_default_shipping: bool = False
    is_default_billing: bool = False

    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )

    user: "User" = Relationship(back_populates="addresses")
