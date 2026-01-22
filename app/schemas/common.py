"""Common Pydantic Schemas."""

from enum import StrEnum
from typing import TypeVar
from uuid import UUID

import phonenumbers
import pycountry
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class UUIDMixin(BaseModel):
    """Mixin to add a UUID primary key."""

    id: UUID

    model_config = ConfigDict(frozen=True)


class Page[T](BaseModel):
    """Pagination information."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(frozen=True)


class SortOrder(StrEnum):
    """Sorting order."""

    ASC = "asc"
    DESC = "desc"


def validate_country(v: str | None) -> str | None:
    """Validate country code using ISO 3166-1 alpha-2 standard."""
    if v is None:
        return v
    v = v.upper()
    if not pycountry.countries.get(alpha_2=v):
        raise ValueError(
            f"Invalid country code: {v}. Must be ISO 3166-1 alpha-2 (e.g., US, FR, CA)"
        )
    return v


def validate_phone_number(v: str | None) -> str | None:
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
