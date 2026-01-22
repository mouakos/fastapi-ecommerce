"""Utility functions for order management."""

from decimal import Decimal

import ulid


def generate_order_number() -> str:
    """Generate a unique order number."""
    return f"ORD-{ulid.new().str}"


def money_format(value: Decimal) -> Decimal:
    """Format a Decimal value to two decimal places for monetary representation."""
    return value.quantize(Decimal("0.01"), rounding="ROUND_HALF_UP")
