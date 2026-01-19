"""Payment processing API routes for Stripe checkout sessions and webhooks."""

from fastapi import APIRouter, HTTPException, Request

from app.api.v1.dependencies import CurrentUserDep, PaymentServiceDep
from app.schemas.payment import PaymentCheckoutSessionCreate, PaymentCheckoutSessionRead

router = APIRouter(prefix="/payments", tags=["Payments"])


# Checkout session creation
@router.post(
    "/checkout-session",
    summary="Create checkout session",
    description="Create a Stripe checkout session for a specific order. Returns the session URL for redirecting the user to complete payment.",
    response_model=PaymentCheckoutSessionRead,
)
async def create_checkout_session(
    data: PaymentCheckoutSessionCreate,
    payment_service: PaymentServiceDep,
    current_user: CurrentUserDep,
) -> PaymentCheckoutSessionRead:
    """Create a checkout session for the specified order ID."""
    return await payment_service.create_checkout_session(current_user.id, data.order_id)


# Webhook endpoints
@router.post(
    "/stripe-webhook",
    summary="Handle Stripe webhooks",
    description="Process Stripe webhook events for payment confirmations and status updates. This endpoint is called by Stripe, not by clients.",
)
async def stripe_webhook(
    request: Request,
    payment_service: PaymentServiceDep,
) -> None:
    """Process Stripe webhook."""
    stripe_signature = request.headers.get("stripe-signature")

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature header.")

    payload = await request.body()

    await payment_service.process_stripe_webhook(payload, stripe_signature)
