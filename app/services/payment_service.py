"""Service for handling payment operations."""

from typing import Any
from uuid import UUID

import stripe

from app.core.config import settings
from app.core.exceptions import (
    InvalidTransitionError,
    OrderNotFoundError,
    PaymentGatewayError,
    PaymentNotFoundError,
    WebhookValidationError,
)
from app.core.logger import logger
from app.interfaces.unit_of_work import UnitOfWork
from app.models.order import OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.utils.datetime import utcnow
from app.utils.stripe import generate_idempotency_key


class PaymentService:
    """Service layer for payment operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow
        stripe.api_key = settings.stripe_api_key

    async def create_checkout_session(
        self, user_id: UUID, order_id: UUID, success_url: str, cancel_url: str
    ) -> str:
        """Create a Stripe Checkout Session for the specified order.

        Args:
            user_id (UUID): ID of the user making the payment.
            order_id (UUID): ID of the order to create checkout session for (must be PENDING).
            success_url (str): URL to redirect to upon successful payment.
            cancel_url (str): URL to redirect to if payment is canceled.

        Returns:
            str: The URL of the Stripe Checkout Session page.

        Raises:
            OrderNotFoundError: If the order is not found.
            InvalidTransitionError: If the order is not in PENDING status.
            PaymentGatewayError: If there is an error creating the Stripe session.
        """
        order = await self.uow.orders.find_user_order(order_id, user_id)
        if not order:
            raise OrderNotFoundError(order_id=order_id, user_id=user_id)

        if order.status != OrderStatus.PENDING:
            raise InvalidTransitionError(
                entity="Order",
                from_state=order.status.value,
                to_state=OrderStatus.PENDING,
            )

        # Create a checkout session with Stripe
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"{item.product_name}",
                            },
                            "unit_amount": int(item.unit_price * 100),  # amount in cents
                        },
                        "quantity": item.quantity,
                    }
                    for item in order.items
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"order_id": str(order_id), "user_id": str(user_id)},
                expires_at=int(
                    (utcnow().timestamp()) + settings.checkout_session_expire_minutes * 60
                ),
                idempotency_key=generate_idempotency_key(user_id, order_id),
            )
        except stripe.error.StripeError as e:
            raise PaymentGatewayError(message=str(e)) from e

        # Create payment record BEFORE user completes payment
        payment = Payment(
            order_id=order_id,
            amount=order.total_amount,
            currency=session.currency,
            payment_method="card",
            session_id=session.id,
        )
        await self.uow.payments.add(payment)
        logger.info(
            "checkout_session_created",
            order_id=str(order_id),
            user_id=str(user_id),
            session_id=session.id,
        )

        return str(session.url)

    async def process_stripe_webhook(self, payload: bytes, stripe_signature: str) -> None:
        """Process Stripe webhook events for payment confirmations.

        Handles checkout.session.completed events to update order status to PAID,
        mark payment as SUCCESS, and reduce product stock.

        Args:
            payload (bytes): Raw webhook event data from Stripe.
            stripe_signature (str): Stripe signature header for event verification.

        Raises:
            WebhookValidationError: If payload is invalid or signature verification fails.
        """
        event = None
        try:
            event = stripe.Webhook.construct_event(  # type: ignore [no-untyped-call]
                payload, stripe_signature, settings.stripe_webhook_secret
            )
        except ValueError as e:
            raise WebhookValidationError(reason="Invalid payload") from e
        except stripe.error.SignatureVerificationError as e:
            raise WebhookValidationError(reason="Invalid signature") from e

        event_type = event["type"]

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            await self._handle_successful_payment(session)

    async def _handle_successful_payment(
        self,
        session: dict[str, Any],
    ) -> None:
        """Handle successful payment from Stripe webhook.

        Updates order status to PAID, marks payment as SUCCESS, and reduces product stock.
        Implements idempotent processing to handle duplicate webhook deliveries safely.

        Args:
            session (dict[str, Any]): Stripe checkout session object from webhook.

        Raises:
            PaymentNotFoundError: If the payment record is not found.
            OrderNotFoundError: If the order is not found.
            InvalidTransitionError: If the order is not in a valid state for payment processing.
        """
        # Update Order Status
        order_id = UUID(session["metadata"]["order_id"])
        user_id = UUID(session["metadata"]["user_id"])
        session_id = session["id"]

        # Find existing payment record (created during checkout)
        payment = await self.uow.payments.find_by_session_id(session_id)
        if not payment:
            raise PaymentNotFoundError(session_id=session_id)

        # Prevent duplicate processing
        if payment.status == PaymentStatus.SUCCESS:
            return  # Already processed

        # Get order and verify ownership
        order = await self.uow.orders.find_user_order(order_id, user_id)
        if not order:
            raise OrderNotFoundError(order_id=order_id, user_id=user_id)

        if order.status == OrderStatus.PAID:
            return  # Idempotent handling

        if order.status != OrderStatus.PENDING:
            raise InvalidTransitionError(
                entity="Order",
                from_state=order.status.value,
                to_state=OrderStatus.PAID,
            )

        order.status = OrderStatus.PAID
        order.paid_at = utcnow()
        await self.uow.orders.update(order)

        # Update payment record to success
        payment.status = PaymentStatus.SUCCESS
        payment.payment_intent_id = session["payment_intent"]
        await self.uow.payments.update(payment)
        logger.info(
            "payment_successful",
            order_id=str(order_id),
            user_id=str(user_id),
            amount=float(payment.amount),
            session_id=session_id,
        )
