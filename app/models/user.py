"""User model for storing user information."""

from datetime import datetime

from sqlmodel import Column, DateTime, Field

from app.models.base import TimestampMixin, UUIDMixin
from app.utils.utc_time import utcnow


class User(UUIDMixin, TimestampMixin, table=True):
    """User model for storing user information."""

    __tablename__ = "users"
    email: str = Field(index=True, unique=True)
    hashed_password: str = Field(exclude=True)
    first_name: str | None
    last_name: str | None
    phone_number: str | None
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False),
    )
