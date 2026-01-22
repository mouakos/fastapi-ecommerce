"""Order management API routes for checkout and order history."""

# mypy: disable-error-code=return-value
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.v1.dependencies import CurrentUserDep, OrderServiceDep
from app.models.order import OrderStatus
from app.schemas.common import Page, SortOrder
from app.schemas.order import OrderCreate, OrderPublic, OrderSortByField
from app.utils.pagination import build_page

router = APIRouter()


@router.get(
    "",
    response_model=Page[OrderPublic],
    summary="List user orders",
    description="Retrieve paginated list of orders for the authenticated user with optional filtering by status and sorting options.",
)
async def get_orders(
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Annotated[OrderStatus | None, Query(description="Filter by order status")] = None,
    sort_by: Annotated[
        OrderSortByField, Query(description="Field to sort by")
    ] = OrderSortByField.CREATED_AT,
    sort_order: Annotated[SortOrder, Query(description="Sort order")] = SortOrder.DESC,
) -> Page[OrderPublic]:
    """Get all orders for the current user."""
    orders, total = await order_service.get_orders(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        sort_by=sort_by.value,
        sort_order=sort_order.value,
    )
    return build_page(items=orders, page=page, size=page_size, total=total)  # type: ignore [arg-type]


@router.post(
    "/place-order",
    response_model=OrderPublic,
    summary="Place order",
    description="Create a new order from the user's cart with specified shipping and billing addresses. The cart will be cleared after successful order creation. Order status will be PENDING until payment is confirmed.",
)
async def create_order(
    data: OrderCreate,
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> OrderPublic:
    """Create a new order for the current user."""
    return await order_service.create_order(current_user.id, data)


@router.get(
    "/{order_id}",
    response_model=OrderPublic,
    summary="Get order details",
    description="Retrieve detailed information about a specific order including items, addresses, and payment status. Only the order owner can access this endpoint.",
)
async def get_order(
    order_id: UUID,
    current_user: CurrentUserDep,
    order_service: OrderServiceDep,
) -> OrderPublic:
    """Get an order by its ID for the current user."""
    return await order_service.get_order(order_id, current_user.id)
