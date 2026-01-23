"""Utility functions for order management."""

import ulid


def generate_order_number() -> str:
    """Generate a unique order number."""
    return f"ORD-{ulid.new().str}"
