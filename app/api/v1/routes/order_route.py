"""Order API routes."""

from uuid import UUID

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUserDep, OrderServiceDep
from app.schemas.order_schema import OrderCreate, OrderRead

order_route = APIRouter(prefix="/orders", tags=["Orders"])


@order_route.post(
    "/checkout/", response_model=OrderRead, summary="Checkout and create a new order."
)
async def checkout_order(
    data: OrderCreate,
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> OrderRead:
    """Checkout and create a new order for the current user."""
    return await order_service.checkout(current_user.id, data)


@order_route.get(
    "/",
    response_model=list[OrderRead],
    summary="List all orders for the current user.",
)
async def list_orders(
    current_user: CurrentUserDep, order_service: OrderServiceDep
) -> list[OrderRead]:
    """List all orders for the current user."""
    return await order_service.list_all(current_user.id)


@order_route.get(
    "/{order_id}/",
    response_model=OrderRead,
    summary="Retrieve an order by its ID for the current user.",
)
async def get_order(
    order_id: UUID,
    _: CurrentUserDep,
    order_service: OrderServiceDep,
) -> OrderRead:
    """Retrieve an order by its ID for the current user."""
    return await order_service.get_by_id(order_id)
