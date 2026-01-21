"""Payment processing API routes for Stripe checkout sessions and webhooks."""

from fastapi import APIRouter, HTTPException, Request, status

from app.api.v1.dependencies import CurrentUserDep, PaymentServiceDep
from app.schemas.payment import PaymentIntentRequest, PaymentIntentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


# Checkout session creation
@router.post(
    "/payment-intent",
    summary="Create Stripe payment intent",
    description="Create a Stripe Payment Intent for a specific order. Returns the client secret needed to complete the payment. The order must be in PENDING status.",
    response_model=PaymentIntentResponse,
)
async def create_payment_intent(
    data: PaymentIntentRequest,
    payment_service: PaymentServiceDep,
    current_user: CurrentUserDep,
) -> PaymentIntentResponse:
    """Create a payment intent for the specified order ID."""
    # These URLs point to API endpoints (for testing without frontend)
    return await payment_service.create_payment_intent(current_user.id, data.order_id)


# Webhook endpoints
@router.post(
    "/stripe-webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Stripe webhook handler",
    description="Process Stripe webhook events for payment confirmations. This endpoint is called by Stripe servers, not by clients.",
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
