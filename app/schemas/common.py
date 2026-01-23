"""Common Pydantic Schemas."""

from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Any, TypeVar
from uuid import UUID

import phonenumbers
import pycountry
from pydantic import BaseModel, ConfigDict, field_validator

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


TWO_DP = Decimal("0.01")


class TwoDecimalBaseModel(BaseModel):
    """BaseModel that quantizes all Decimal fields to two decimal places."""

    @field_validator("*", mode="before")
    @classmethod
    def _quantize_all_decimals(cls, v: Any) -> Any:  # noqa: ANN401
        """Quantize Decimal fields to two decimal places."""
        if isinstance(v, Decimal):
            return v.quantize(TWO_DP, rounding=ROUND_HALF_UP)
        return v

    model_config = ConfigDict(frozen=True)


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
