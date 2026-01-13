"""User model for storing user information."""

from enum import StrEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLEnum
from sqlmodel import Column, Field, Relationship

from app.models.base import ModelBase, TimestampMixin

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.cart import Cart
    from app.models.order import Order
    from app.models.review import Review
    from app.models.wishlist_item import WishlistItem


class UserRole(StrEnum):
    """Enumeration for user roles."""

    USER = "user"
    ADMIN = "admin"


class User(ModelBase, TimestampMixin, table=True):
    """User model for storing user information."""

    __tablename__ = "users"
    email: str = Field(index=True, unique=True)
    hashed_password: str = Field(exclude=True)
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    role: UserRole = Field(
        default=UserRole.USER,
        sa_column=Column(
            SQLEnum(
                UserRole,
                values_callable=lambda x: [e.value for e in x],
                native_enum=False,
                create_constraint=True,
                length=50,
                validate_strings=True,
                name="user_role",
            ),
            nullable=False,
            index=True,
        ),
    )
    is_superuser: bool = Field(default=False)

    # Relationships
    addresses: list["Address"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    cart: Optional["Cart"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )
    orders: list["Order"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    wishlist_items: list["WishlistItem"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
    reviews: list["Review"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}, cascade_delete=True
    )
