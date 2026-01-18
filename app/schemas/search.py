"""Schemas for search functionality."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AvailabilityFilter(StrEnum):
    """Filters for product availability."""

    ALL = "all"
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"


class SortByField(StrEnum):
    """Fields to sort products by."""

    NAME = "name"
    PRICE = "price"
    RATING = "rating"
    POPULARITY = "popularity"
    CREATED_AT = "created_at"


class ReviewSortByField(StrEnum):
    """Fields to sort product reviews by."""

    RATING = "rating"
    STATUS = "status"
    CREATED_AT = "created_at"


class OrderSortByField(StrEnum):
    """Fields to sort orders by."""

    TOTAL_AMOUNT = "total_amount"
    STATUS = "status"
    CREATED_AT = "created_at"


class UserSortByField(StrEnum):
    """Fields to sort users by."""

    EMAIL = "email"
    ROLE = "role"
    CREATED_AT = "created_at"


class SortOrder(StrEnum):
    """Sorting order."""

    ASC = "asc"
    DESC = "desc"


class ProductAutocompleteRead(BaseModel):
    """Schema for product name autocomplete suggestions."""

    suggestions: list[str] = Field(..., description="List of product name suggestions (max 10)")

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "suggestions": [
                        "iPhone 16 Pro",
                        "iPhone 16",
                        "iPhone 15 Pro Max",
                        "iPhone 14",
                    ]
                }
            ]
        },
    )
