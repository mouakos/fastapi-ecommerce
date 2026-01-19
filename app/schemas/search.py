"""Schemas for search functionality."""

from enum import StrEnum


class ProductAvailabilityFilter(StrEnum):
    """Filters for product availability."""

    ALL = "all"
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"


class ProductSortByField(StrEnum):
    """Fields to sort products by."""

    NAME = "name"
    PRICE = "price"
    RATING = "rating"
    POPULARITY = "popularity"
    CREATED_AT = "created_at"


class ReviewAdminSortByField(StrEnum):
    """Fields to sort product reviews by."""

    RATING = "rating"
    STATUS = "status"
    CREATED_AT = "created_at"


class ReviewSortByField(StrEnum):
    """Fields to sort product reviews by."""

    RATING = "rating"
    CREATED_AT = "created_at"


class OrderSortByField(StrEnum):
    """Fields to sort orders by."""

    TOTAL_AMOUNT = "total_amount"
    STATUS = "status"
    CREATED_AT = "created_at"


class UserAdminSortByField(StrEnum):
    """Fields to sort users by."""

    EMAIL = "email"
    ROLE = "role"
    CREATED_AT = "created_at"


class SortOrder(StrEnum):
    """Sorting order."""

    ASC = "asc"
    DESC = "desc"
