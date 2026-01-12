"""Enumeration definitions."""

from enum import StrEnum


class OrderStatus(StrEnum):
    """Enumeration for order statuses."""

    PENDING = "pending"
    PROCESSING = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"
