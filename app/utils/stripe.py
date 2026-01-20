"""Stripe utility functions for payment processing."""

import hashlib
from uuid import UUID


def generate_idempotency_key(user_id: UUID, order_id: UUID) -> str:
    """Generate a unique idempotency key for Stripe requests.

    This prevents duplicate charges if the same request is made multiple times.
    Stripe uses idempotency keys to safely retry requests without performing
    the same operation twice.

    Args:
        user_id (UUID): The ID of the user making the payment.
        order_id (UUID): The ID of the order for which to create the payment.

    Returns:
        str: A unique idempotency key for the Stripe request.
    """
    combined = f"{user_id}:{order_id}"
    return hashlib.sha256(combined.encode()).hexdigest()
