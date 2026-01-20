"""Utility to generate SKU codes."""

import ulid


def generate_sku(prefix: str = "PRD") -> str:
    """Generate a unique SKU code with a given prefix."""
    return f"{prefix}-{ulid.new().str}"
