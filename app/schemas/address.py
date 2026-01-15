"""Schemas for address management."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import UUIDMixin


class AddressBase(BaseModel):
    """Base schema for Address."""

    full_name: str = Field(..., max_length=100, min_length=2)
    company: str | None = Field(None, max_length=100, min_length=2)
    line1: str = Field(..., max_length=255, min_length=2)
    line2: str | None = Field(None, max_length=255, min_length=2)
    city: str = Field(..., max_length=100, min_length=2)
    state: str | None = Field(None, max_length=100, min_length=2)
    postal_code: str = Field(..., max_length=20, min_length=2)
    country: str = Field(..., max_length=100, min_length=2)
    phone_number: str | None = Field(None, max_length=20)


class AddressCreate(AddressBase):
    """Schema for creating a new address."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
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
            }
        },
    )


class AddressRead(AddressCreate, UUIDMixin):
    """Schema for reading address information."""

    user_id: UUID

    model_config = ConfigDict(frozen=True)


class AddressUpdate(BaseModel):
    """Partial update payload for an address."""

    full_name: str | None = Field(None, max_length=100, min_length=2)
    company: str | None = Field(None, max_length=100, min_length=2)
    line1: str | None = Field(None, max_length=100, min_length=2)
    line2: str | None = Field(None, max_length=100, min_length=2)
    city: str | None = Field(None, max_length=100, min_length=2)
    state: str | None = Field(None, max_length=100, min_length=2)
    postal_code: str | None = Field(None, max_length=20, min_length=2)
    country: str | None = Field(None, max_length=100, min_length=2)
    phone_number: str | None = Field(None, max_length=20)

    model_config = ConfigDict(frozen=True)
