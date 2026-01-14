"""Schemas for search functionality."""

from enum import StrEnum


class AvailabilityFilter(StrEnum):
    """Filters for product availability."""

    ALL = "all"
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"


class SortByField(StrEnum):
    """Fields to sort products by."""

    ID = "id"
    NAME = "name"
    PRICE = "price"
    RATING = "rating"
    POPULARITY = "popularity"
    CREATED_AT = "created_at"


class SortOrder(StrEnum):
    """Sorting order."""

    ASC = "asc"
    DESC = "desc"
