"""Cart schema for managing shopping cart data."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, computed_field

from app.schemas.common import UUIDMixin


class CartItemCreate(BaseModel):
    """Schema for creating a new cart item."""

    product_id: UUID
    quantity: int = Field(default=1, ge=1)

    model_config = ConfigDict(frozen=True)


class CartItemUpdate(BaseModel):
    """Schema for updating a cart item."""

    quantity: int = Field(..., ge=1)
    model_config = ConfigDict(frozen=True)


class CartItemRead(BaseModel):
    """Schema for reading cart items."""

    product_id: UUID
    quantity: int
    unit_price: Decimal = Field(
        ..., description="Price per unit of the product", decimal_places=2, max_digits=10
    )
    product_name: str = Field(..., max_length=255)
    image_url: HttpUrl | None

    @computed_field(return_type=Decimal)
    def subtotal(self) -> Decimal:
        """Calculate subtotal for the cart item."""
        return self.quantity * self.unit_price

    model_config = ConfigDict(frozen=True)


class CartRead(UUIDMixin):
    """Schema for reading cart."""

    user_id: UUID | None = None
    items: list[CartItemRead] = []

    @computed_field(return_type=Decimal)
    def subtotal(self) -> Decimal:
        """Calculate total price for the cart."""
        return sum((item.quantity * item.unit_price for item in self.items), start=Decimal("0.00"))

    @computed_field(return_type=int)
    def total_items(self) -> int:
        """Calculate total number of items in the cart."""
        return sum(item.quantity for item in self.items)

    model_config = ConfigDict(frozen=True)
