"""Payment processing API routes for Stripe checkout sessions and webhooks."""

from fastapi import APIRouter, HTTPException, Request, status

from app.api.v1.dependencies import CurrentUserDep, PaymentServiceDep
from app.core.config import settings
from app.schemas.payment import CheckoutRequest, CheckoutResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


# Checkout session creation
@router.post(
    "/checkout-session",
    summary="Create Stripe checkout session",
    description="Create a Stripe Checkout Session for a specific order. Returns the hosted checkout page URL where the user can securely complete payment. The order must be in PENDING status.",
    response_model=CheckoutResponse,
)
async def create_checkout_session(
    data: CheckoutRequest,
    payment_service: PaymentServiceDep,
    current_user: CurrentUserDep,
) -> CheckoutResponse:
    """Create a checkout session for the specified order ID."""
    # These URLs point to API endpoints (for testing without frontend)
    cancel_url = settings.domain + "/api/v1/payments/cancel"
    success_url = settings.domain + "/api/v1/payments/success?session_id={CHECKOUT_SESSION_ID}"
    checkout_url = await payment_service.create_checkout_session(
        current_user.id, data.order_id, success_url, cancel_url
    )
    return CheckoutResponse(checkout_url=checkout_url)


# Webhook endpoints
@router.post(
    "/stripe-webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Stripe webhook handler",
    description="Process Stripe webhook events for payment confirmations. Handles checkout.session.completed events to update order status and reduce product stock. This endpoint is called by Stripe servers, not by clients.",
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


# --- Example Success/Cancel Pages (Optional, just for testing browser flow) ---
@router.get(
    "/success",
    response_model=str,
    summary="Payment success redirect",
    description="Redirect page after successful payment completion. For testing purposes only - production should redirect to a frontend URL.",
)
def success_page(session_id: str) -> str:
    """Example success page after payment."""
    return f"Payment Successful! Session ID: {session_id}"


@router.get(
    "/cancel",
    response_model=str,
    summary="Payment cancellation redirect",
    description="Redirect page when payment is cancelled by user. For testing purposes only - production should redirect to a frontend URL.",
)
def cancel_page() -> str:
    """Example cancel page after payment."""
    return "Payment Canceled!"
