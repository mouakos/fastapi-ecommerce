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

    # Relationships
    user: "User" = Relationship(
        back_populates="addresses", sa_relationship_kwargs={"lazy": "selectin"}
    )
