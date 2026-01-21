"""Service for handling payment operations."""

from typing import Any
from uuid import UUID

import stripe

from app.core.config import settings
from app.core.exceptions import (
    InvalidOrderStatusError,
    OrderNotFoundError,
    PaymentGatewayError,
    WebhookValidationError,
)
from app.core.logger import logger
from app.interfaces.unit_of_work import UnitOfWork
from app.models.order import OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentIntentResponse
from app.utils.datetime import utcnow
from app.utils.stripe import generate_idempotency_key


class PaymentService:
    """Service layer for payment operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow
        stripe.api_key = settings.stripe_api_key

    async def create_payment_intent(self, user_id: UUID, order_id: UUID) -> PaymentIntentResponse:
        """Create a Stripe Checkout Session for the specified order.

        Args:
            user_id (UUID): ID of the user making the payment.
            order_id (UUID): ID of the order to create checkout session for (must be PENDING).

        Returns:
            PaymentIntentResponse: The response containing payment intent details.

        Raises:
            OrderNotFoundError: If the order is not found.
            InvalidOrderStatusError: If the order is not in PENDING status.
            PaymentGatewayError: If there is an error creating the Stripe session.
        """
        order = await self.uow.orders.find_user_order(order_id, user_id)
        if not order:
            raise OrderNotFoundError(order_id=order_id, user_id=user_id)

        if order.status != OrderStatus.PENDING:
            raise InvalidOrderStatusError(
                message="Checkout session can only be created for orders in 'pending' status.",
                current_status=order.status.value,
            )

        # Create Stripe PaymentIntent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Amount in cents
                currency="usd",
                metadata={"order_id": str(order.id), "user_id": str(user_id)},
                idempotency_key=generate_idempotency_key(order.id, user_id),
                automatic_payment_methods={"enabled": True},
            )
        except stripe.error.StripeError as e:
            raise PaymentGatewayError(message=str(e)) from e

        payment = Payment(
            order_id=order_id,
            amount=order.total_amount,
            currency=intent.currency,
            payment_method="stripe",
            transaction_id=intent.id,
        )
        await self.uow.payments.add(payment)

        payment_intent_response = PaymentIntentResponse(
            client_secret=intent.client_secret,  # type: ignore [arg-type]
            intent_id=intent.id,
            amount=order.total_amount,
            currency=intent.currency,
        )
        logger.info(
            "payment_intent_created",
            order_id=str(order_id),
            user_id=str(user_id),
            transaction_id=intent.id,
        )
        return payment_intent_response

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

        if event_type == "payment_intent.succeeded":
            transaction_intent = event["data"]["object"]
            await self._handle_successful_payment(transaction_intent)
        elif event_type == "payment_intent.payment_failed":
            transaction_intent = event["data"]["object"]
            await self._handle_failed_payment(transaction_intent)

    async def _handle_successful_payment(
        self,
        transaction_intent: dict[str, Any],
    ) -> None:
        """Handle successful payment from Stripe webhook.

        Updates order status to PAID, marks payment as SUCCESS, and reduces product stock.
        Implements idempotent processing to handle duplicate webhook deliveries safely.

        Args:
            transaction_intent (dict[str, Any]): Stripe payment intent object from webhook.
        """
        user_id = UUID(transaction_intent["metadata"]["user_id"])
        transaction_id = transaction_intent["id"]

        # Find existing payment record (created during checkout)
        payment = await self.uow.payments.find_by_transaction_id(transaction_id=transaction_id)
        if not payment:
            logger.warning(
                "payment_not_found",
                transaction_id=transaction_id,
                user_id=str(user_id),
            )
            return  # Ignore unknown payments

        # Prevent duplicate processing
        if payment.status == PaymentStatus.SUCCESS:
            logger.info(
                "payment_already_processed",
                order_id=str(payment.order_id),
                user_id=str(user_id),
                transaction_id=payment.transaction_id,
            )
            return  # Already processed, do nothing

        # Update payment status to SUCCESS
        payment.status = PaymentStatus.SUCCESS
        await self.uow.payments.update(payment)

        # Get order and verify ownership
        order = await self.uow.orders.find_user_order(payment.order_id, user_id)
        if not order:
            logger.warning(
                "order_not_found_for_payment",
                order_id=str(payment.order_id),
                user_id=str(user_id),
            )
            return  # Ignore if order not found

        order.status = OrderStatus.PAID
        order.paid_at = utcnow()
        await self.uow.orders.update(order)

        logger.info(
            "payment_successful",
            order_id=str(order.id),
            user_id=str(user_id),
            transaction_id=payment.transaction_id,
        )

    async def _handle_failed_payment(
        self,
        transaction_intent: dict[str, Any],
    ) -> None:
        """Handle failed payment from Stripe webhook.

        Args:
            transaction_intent (dict[str, Any]): Stripe payment intent object from webhook.
        """
        transaction_id = transaction_intent["id"]
        user_id = UUID(transaction_intent["metadata"]["user_id"])

        # Find existing payment record (created during checkout)
        payment = await self.uow.payments.find_by_transaction_id(transaction_id=transaction_id)
        if not payment:
            logger.warning(
                "payment_not_found",
                transaction_id=transaction_id,
                user_id=str(user_id),
            )
            return  # Ignore unknown payments

        payment.status = PaymentStatus.FAILED
        await self.uow.payments.update(payment)
        logger.warning(
            "payment_failed",
            order_id=str(payment.order_id),
            user_id=str(user_id),
            transaction_id=payment.transaction_id,
        )
