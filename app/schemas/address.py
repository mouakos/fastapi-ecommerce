"""Schemas for address management."""

from uuid import UUID

import phonenumbers
import pycountry
from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    country: str = Field(
        ...,
        description="ISO 3166-1 alpha-2 country code (e.g., US, FR, CA)",
    )
    phone_number: str | None = Field(None, max_length=20)

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Validate country code using ISO 3166-1 alpha-2 standard."""
        v = v.upper()
        if not pycountry.countries.get(alpha_2=v):
            raise ValueError(
                f"Invalid country code: {v}. Must be ISO 3166-1 alpha-2 (e.g., US, FR, CA)"
            )
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str | None) -> str | None:
        """Validate phone number format using international E.164 standard."""
        if v is None:
            return v
        try:
            parsed = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(
                    f"Invalid phone number: {v}. Must be in E.164 format (e.g., +1234567890)"
                )
            # Return formatted phone number
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException as e:
            raise ValueError(
                f"Invalid phone number format: {v}. Must include country code (e.g., +1234567890)"
            ) from e


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
                "phone_number": "+4917612345678",
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
    country: str | None = Field(
        None,
        description="ISO 3166-1 alpha-2 country code (e.g., US, FR, CA)",
    )
    phone_number: str | None = Field(None, max_length=20)

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str | None) -> str | None:
        """Validate country code using ISO 3166-1 alpha-2 standard."""
        if v is None:
            return v
        v = v.upper()
        if not pycountry.countries.get(alpha_2=v):
            raise ValueError(
                f"Invalid country code: {v}. Must be ISO 3166-1 alpha-2 (e.g., US, FR, CA)"
            )
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str | None) -> str | None:
        """Validate phone number format using international E.164 standard."""
        if v is None:
            return v
        try:
            parsed = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(
                    f"Invalid phone number: {v}. Must be in E.164 format (e.g., +1234567890)"
                )
            # Return formatted phone number
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException as e:
            raise ValueError(
                f"Invalid phone number format: {v}. Must include country code (e.g., +1234567890)"
            ) from e

    model_config = ConfigDict(frozen=True)
