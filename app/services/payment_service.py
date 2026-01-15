"""Service for handling payment operations."""

from datetime import datetime
from typing import Any
from uuid import UUID

import stripe
from fastapi import HTTPException

from app.core.config import settings
from app.interfaces.unit_of_work import UnitOfWork
from app.models.order import OrderStatus
from app.models.payment import Currency, Payment, PaymentMethod, PaymentStatus
from app.schemas.payment import PaymentCheckoutSessionRead
from app.utils.utc_time import utcnow


class PaymentService:
    """Service layer for payment operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def create_checkout_session(
        self, user_id: UUID, order_id: UUID
    ) -> PaymentCheckoutSessionRead:
        """Create a checkout session for the given order ID.

        Args:
            user_id (UUID): The ID of the user making the payment.
            order_id (UUID): The ID of the order for which to create the checkout session.

        Returns:
            str: The URL of the created checkout session.
        """
        order = await self.uow.orders.get_by_id(order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=404, detail="Order not found.")

        if order.status == OrderStatus.PAID:
            raise HTTPException(status_code=400, detail="Order is already paid.")

        # Create a checkout session with Stripe
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"Order {order_id}",
                            },
                            "unit_amount": int(order.total_amount * 100),  # amount in cents
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=settings.domain + "/payment-success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.domain + "/payment-cancelled",
                metadata={"order_id": str(order_id), "user_id": str(user_id)},
            )
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}") from e

        new_payment = Payment(
            order_id=order_id,
            currency=Currency.USD,
            amount=order.total_amount,
            payment_method=PaymentMethod.CARD,
            status=PaymentStatus.PENDING,
            session_id=session.id,
        )
        await self.uow.payments.add(new_payment)

        return PaymentCheckoutSessionRead(
            checkout_url=str(session.url),
            session_id=session.id,
            amount=order.total_amount,
            currency=Currency.USD,
            expires_at=datetime.fromtimestamp(session.expires_at),
            order_id=order_id,
        )

    async def process_webhook(self, payload: bytes, stripe_signature: str) -> None:
        """Process webhook events.

        Args:
            payload (bytes): The data from the webhook event.
            stripe_signature (str): The Stripe signature for verifying the event.
        """
        event = None
        try:
            event = stripe.Webhook.construct_event(  # type: ignore [no-untyped-call]
                payload, stripe_signature, settings.stripe_webhook_secret
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload") from e
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail="Invalid signature") from e

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            await self._handle_successful_payment(session)
        elif event["type"] == "checkout.session.expired":
            session = event["data"]["object"]
            await self._handle_failed_payment(session)

    async def _process_payment_webhook(
        self,
        session: dict[str, Any],
        target_payment_status: PaymentStatus,
        target_order_status: OrderStatus,
    ) -> None:
        """Process payment webhook and update payment and order status.

        Args:
            session (dict[str, Any]): The webhook session data.
            target_payment_status (PaymentStatus): The status to set for the payment.
            target_order_status (OrderStatus): The status to set for the order.
        """
        session_id = session["id"]
        payment = await self.uow.payments.get_by_session_id(session_id)

        if not payment:
            raise HTTPException(
                status_code=500,
                detail="Payment record not found for this checkout session.",
            )

        # Idempotency check: if payment is already processed, skip
        if payment.status == target_payment_status:
            return

        # Update payment status
        payment.status = target_payment_status
        await self.uow.payments.update(payment)

        # Update Order Status
        order = await self.uow.orders.get_by_id(payment.order_id)
        if not order:
            raise HTTPException(
                status_code=500,
                detail="Order not found for payment - data inconsistency.",
            )

        order.payment_status = target_payment_status
        order.status = target_order_status
        if target_order_status == OrderStatus.PAID:
            order.paid_at = utcnow()
        await self.uow.orders.update(order)

    async def _handle_successful_payment(self, session: dict[str, Any]) -> None:
        """Handle successful payment processing.

        Args:
            session (dict[str, Any]): The successful payment session data.
        """
        await self._process_payment_webhook(session, PaymentStatus.SUCCESS, OrderStatus.PAID)

    async def _handle_failed_payment(self, session: dict[str, Any]) -> None:
        """Handle failed payment processing.

        Args:
            session (dict[str, Any]): The data of the failed payment session.
        """
        await self._process_payment_webhook(session, PaymentStatus.FAILED, OrderStatus.PENDING)
