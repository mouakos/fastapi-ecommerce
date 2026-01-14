"""API routes for cart operations."""

from uuid import UUID

from fastapi import APIRouter

from app.api.v1.dependencies import (
    CartServiceDep,
    CartSessionIdOrCreateDep,
    OptionalCurrentUserDep,
)
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate, CartRead

cart_router = APIRouter(prefix="/cart", tags=["Cart"])


@cart_router.get("/", response_model=CartRead, summary="Get current user's cart or session cart")
async def get_cart(
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> CartRead:
    """Get the current user's cart or session cart."""
    return await cart_service.get_or_create(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
    )


@cart_router.post("/items/", response_model=CartRead, summary="Add item to cart")
async def add_item(
    data: CartItemCreate,
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> CartRead:
    """Add an item to the cart."""
    return await cart_service.add_item(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        data=data,
    )


@cart_router.put(
    "/items/{product_id}/", response_model=CartRead, summary="Update cart item quantity"
)
async def update_item(
    product_id: UUID,
    data: CartItemUpdate,
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> CartRead:
    """Update the quantity of a cart item."""
    return await cart_service.update_item(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        product_id=product_id,
        data=data,
    )


@cart_router.delete(
    "/items/{product_id}/", response_model=CartRead, summary="Remove item from cart"
)
async def remove_item(
    product_id: UUID,
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> CartRead:
    """Remove an item from the cart."""
    return await cart_service.remove_item(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        product_id=product_id,
    )


@cart_router.delete("/", response_model=CartRead, summary="Clear cart")
async def clear_cart(
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> CartRead:
    """Clear all items from the cart."""
    return await cart_service.clear(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
    )
