"""Schemas for address management."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import TimestampMixin, UUIDMixin


class AddressBase(BaseModel):
    """Base schema for Address."""

    full_name: str = Field(..., max_length=100, min_length=2)
    company: str | None = Field(None, max_length=100, min_length=2)
    line1: str = Field(..., max_length=200, min_length=2)
    line2: str | None = Field(None, max_length=200, min_length=2)
    city: str = Field(..., max_length=100, min_length=2)
    state: str | None = Field(None, max_length=100, min_length=2)
    postal_code: str = Field(..., max_length=20, min_length=2)
    country: str = Field(..., max_length=20, min_length=2)
    phone_number: str | None = Field(None, max_length=20)
    is_default_shipping: bool = False
    is_default_billing: bool = False


class AddressCreate(AddressBase):
    """Schema for creating a new address."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "full_name": "John Doe",
                "company": "Acme Inc.",
                "line1": "123 Main Street",
                "line2": "Apt 4B",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "phone_number": "+1234567890",
                "is_default_shipping": True,
                "is_default_billing": False,
            }
        }
    }


class AddressRead(AddressCreate, UUIDMixin, TimestampMixin):
    """Schema for reading address information."""

    user_id: UUID


class AddressUpdate(BaseModel):
    """Partial update payload for an address."""

    full_name: str | None = Field(None, max_length=100, min_length=2)
    last_name: str | None = Field(None, max_length=100, min_length=2)
    company: str | None = Field(None, max_length=100, min_length=2)
    line1: str | None = Field(None, max_length=200, min_length=2)
    line2: str | None = Field(None, max_length=200, min_length=2)
    city: str | None = Field(None, max_length=100, min_length=2)
    state: str | None = Field(None, max_length=100, min_length=2)
    postal_code: str | None = Field(None, max_length=20, min_length=2)
    country: str | None = Field(None, max_length=20, min_length=2)
    phone_number: str | None = Field(None, max_length=20)
    is_default_shipping: bool | None = None
    is_default_billing: bool | None = None
