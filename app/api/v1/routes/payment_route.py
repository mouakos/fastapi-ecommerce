"""API routes for payment operations."""

from fastapi import APIRouter, HTTPException, Request

from app.api.v1.dependencies import CurrentUserDep, PaymentServiceDep
from app.schemas.payment_schema import PaymentCheckoutSessionCreate, PaymentCheckoutSessionRead

payment_route = APIRouter(prefix="/payments", tags=["Payments"])


@payment_route.post(
    "/checkout-session/",
    summary="Create a checkout session for an order.",
    response_model=PaymentCheckoutSessionRead,
)
async def create_checkout_session(
    data: PaymentCheckoutSessionCreate,
    payment_service: PaymentServiceDep,
    current_user: CurrentUserDep,
) -> PaymentCheckoutSessionRead:
    """Create a checkout session for the specified order ID."""
    return await payment_service.create_checkout_session(current_user.id, data.order_id)


@payment_route.post(
    "/webhooks/stripe",
    summary="Handle Stripe webhook events.",
)
async def webhook(
    request: Request,
    payment_service: PaymentServiceDep,
) -> None:
    """Process webhook."""
    stripe_signature = request.headers.get("stripe-signature")

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature header.")

    payload = await request.body()

    await payment_service.process_webhook(payload, stripe_signature)
