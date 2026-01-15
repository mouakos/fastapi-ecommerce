"""Address model for storing user address information."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.common import ModelBase, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Address(ModelBase, TimestampMixin, table=True):
    """Address model for storing user address information."""

    __tablename__ = "addresses"
    user_id: UUID = Field(index=True, foreign_key="users.id", ondelete="CASCADE")
    full_name: str = Field(max_length=100)
    company: str | None = Field(None, max_length=100)
    line1: str = Field(max_length=255)
    line2: str | None = Field(None, max_length=255)
    city: str = Field(max_length=100)
    state: str | None = Field(None, max_length=100)
    postal_code: str = Field(max_length=20)
    country: str = Field(max_length=100)
    phone_number: str | None = Field(None, max_length=20)
    is_default_shipping: bool = False
    is_default_billing: bool = False

    # Relationships
    user: "User" = Relationship(
        back_populates="addresses", sa_relationship_kwargs={"lazy": "selectin"}
    )
