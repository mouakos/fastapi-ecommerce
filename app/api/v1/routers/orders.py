"""Order API routes."""

from uuid import UUID

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUserDep, OrderServiceDep
from app.schemas.order import OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["Orders"])


# Collection paths
@router.get(
    "",
    response_model=list[OrderRead],
    summary="List orders",
    description="Retrieve all orders for the authenticated user, sorted by creation date (newest first).",
)
async def list_orders(
    current_user: CurrentUserDep, order_service: OrderServiceDep
) -> list[OrderRead]:
    """List all orders for the current user."""
    return await order_service.list_all(current_user.id)


@router.post(
    "/checkout",
    response_model=OrderRead,
    summary="Checkout and create order",
    description="Create a new order from the user's cart and specified shipping/billing addresses. The cart will be emptied after successful order creation.",
)
async def checkout_order(
    data: OrderCreate,
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> OrderRead:
    """Checkout and create a new order for the current user."""
    return await order_service.checkout(current_user.id, data)


# Single order paths
@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Get order by ID",
    description="Retrieve detailed information about a specific order. Only the order owner can access this endpoint.",
)
async def get_order(
    order_id: UUID,
    _: CurrentUserDep,
    order_service: OrderServiceDep,
) -> OrderRead:
    """Retrieve an order by its ID for the current user."""
    return await order_service.get_by_id(order_id)
