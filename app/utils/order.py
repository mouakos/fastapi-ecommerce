"""Utility functions for order management."""

import ulid

from app.models.order import OrderStatus
from app.models.payment import PaymentStatus

_ALLOWED_ORDER_STATUS_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELED: set(),
}

_ALLOWED_PAYMENT_STATUS_TRANSITIONS = {
    PaymentStatus.PENDING: {PaymentStatus.SUCCESS, PaymentStatus.FAILED},
    PaymentStatus.SUCCESS: set(),
    PaymentStatus.FAILED: set(),
}


def generate_order_number() -> str:
    """Generate a unique order number."""
    return f"ORD-{ulid.new().str}"


def is_valid_order_status_transition(
    current_status: OrderStatus,
    new_status: OrderStatus,
) -> bool:
    """Check if the transition from current_status to new_status is valid."""
    allowed_transitions = _ALLOWED_ORDER_STATUS_TRANSITIONS.get(current_status, set())
    return new_status in allowed_transitions


def is_valid_payment_status_transition(
    current_status: PaymentStatus,
    new_status: PaymentStatus,
) -> bool:
    """Check if the transition from current_status to new_status is valid."""
    allowed_transitions = _ALLOWED_PAYMENT_STATUS_TRANSITIONS.get(current_status, set())
    return new_status in allowed_transitions
