"""Service for handling payment operations."""

import hashlib
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
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentIntentResponse
from app.utils.datetime import utcnow


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
                order_id=order_id,
                current_status=order.status.value,
                expected_status=OrderStatus.PENDING.value,
            )

        # Create Stripe PaymentIntent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Amount in cents
                currency="usd",
                metadata={"order_id": str(order.id), "user_id": str(user_id)},
                idempotency_key=self.generate_idempotency_key(user_id, order.id),
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

    async def process_stripe_webhook(self, payload: bytes, stripe_signature: str | None) -> None:
        """Process Stripe webhook events for payment confirmations.

        Handles checkout.session.completed events to update order status to PAID,
        mark payment as SUCCESS, and reduce product stock.

        Args:
            payload (bytes): Raw webhook event data from Stripe.
            stripe_signature (str | None): Stripe signature header for event verification.

        Raises:
            WebhookValidationError: If the webhook payload or signature is invalid.
        """
        if not stripe_signature:
            raise WebhookValidationError(reason="Missing Stripe signature")
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
        else:
            logger.info("stripe_webhook_ignored", event_type=event_type)

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
        transaction_id = transaction_intent["id"]
        user_id = transaction_intent["metadata"]["user_id"]

        # Find existing payment record (created during checkout)
        payment = await self.uow.payments.find_by_transaction_id(transaction_id=transaction_id)
        if not payment:
            logger.warning(
                "payment_not_found",
                transaction_id=transaction_id,
                user_id=user_id,
            )
            return  # Ignore unknown payments

        # Prevent duplicate processing
        if payment.status == PaymentStatus.SUCCESS:
            logger.info(
                "payment_already_processed",
                order_id=str(payment.order_id),
                user_id=user_id,
                transaction_id=payment.transaction_id,
            )
            return  # Already processed, do nothing

        order = await self.uow.orders.find_by_id(payment.order_id)
        if not order:
            logger.warning(
                "order_not_found_for_payment",
                order_id=str(payment.order_id),
                user_id=user_id,
                transaction_id=payment.transaction_id,
            )
            return

        if order.user_id != user_id:
            logger.warning(
                "payment_user_mismatch",
                order_id=str(order.id),
                user_id=user_id,
                order_user_id=str(order.user_id),
                transaction_id=payment.transaction_id,
            )
            return

        # Update payment status to SUCCESS
        payment.status = PaymentStatus.SUCCESS
        await self.uow.payments.update(payment)

        if order.status == OrderStatus.PAID:
            logger.info(
                "order_already_paid",
                order_id=str(order.id),
                user_id=str(user_id),
                transaction_id=payment.transaction_id,
            )
            return

        if order.status != OrderStatus.PENDING:
            logger.warning(
                "order_not_payable",
                order_id=str(order.id),
                user_id=str(user_id),
                current_status=order.status.value,
                transaction_id=payment.transaction_id,
            )
            return

        order.status = OrderStatus.PAID
        order.paid_at = utcnow()
        await self.uow.orders.update(order)

        # Reduce product stock levels
        await self._update_stock(order)

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
        user_id = transaction_intent["metadata"]["user_id"]

        # Find existing payment record (created during checkout)
        payment = await self.uow.payments.find_by_transaction_id(transaction_id=transaction_id)
        if not payment:
            logger.warning(
                "payment_not_found",
                transaction_id=transaction_id,
                user_id=user_id,
            )
            return  # Ignore unknown payments

        payment.status = PaymentStatus.FAILED
        await self.uow.payments.update(payment)
        logger.warning(
            "payment_failed",
            order_id=str(payment.order_id),
            user_id=user_id,
            transaction_id=payment.transaction_id,
        )

    async def _update_stock(self, order: Order) -> None:
        """Update stock levels for products in the order.

        Args:
            order (Order): The order containing items to update stock for.
        """
        for item in order.items:
            product = item.product
            product.stock -= item.quantity
            await self.uow.products.update(product)
            logger.info(
                "product_stock_updated",
                product_id=str(product.id),
                new_stock=product.stock,
            )

    def generate_idempotency_key(self, user_id: UUID, order_id: UUID) -> str:
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
