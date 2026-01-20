"""Service for handling payment operations."""

from typing import Any
from uuid import UUID

import stripe
from fastapi import HTTPException

from app.core.config import settings
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
            HTTPException: If order is not found, not in PENDING status, or Stripe API fails.
        """
        order = await self.uow.orders.find_user_order(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")

        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create checkout session for order with status: {order.status}",
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
            raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}") from e

        # Create payment record BEFORE user completes payment
        payment = Payment(
            order_id=order_id,
            amount=order.total_amount,
            currency=session.currency,
            payment_method="card",
            session_id=session.id,
        )
        await self.uow.payments.add(payment)

        return str(session.url)

    async def process_stripe_webhook(self, payload: bytes, stripe_signature: str) -> None:
        """Process Stripe webhook events for payment confirmations.

        Handles checkout.session.completed events to update order status to PAID,
        mark payment as SUCCESS, and reduce product stock.

        Args:
            payload (bytes): Raw webhook event data from Stripe.
            stripe_signature (str): Stripe signature header for event verification.

        Raises:
            HTTPException: If payload is invalid, signature verification fails, or processing errors occur.
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
            HTTPException: If payment/order not found or invalid status transition.
        """
        # Update Order Status
        order_id = UUID(session["metadata"]["order_id"])
        user_id = UUID(session["metadata"]["user_id"])
        session_id = session["id"]

        # Find existing payment record (created during checkout)
        payment = await self.uow.payments.find_by_session_id(session_id)
        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found for this session.",
            )

        # Prevent duplicate processing
        if payment.status == PaymentStatus.SUCCESS:
            return  # Already processed

        # Get order and verify ownership
        order = await self.uow.orders.find_user_order(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")

        if order.status == OrderStatus.PAID:
            return  # Idempotent handling

        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot process payment for order with status: {order.status}",
            )

        order.status = OrderStatus.PAID
        order.paid_at = utcnow()
        await self.uow.orders.update(order)

        # Update payment record to success
        payment.status = PaymentStatus.SUCCESS
        payment.payment_intent_id = session["payment_intent"]
        await self.uow.payments.update(payment)
