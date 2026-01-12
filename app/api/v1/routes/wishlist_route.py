"""Routes for managing wishlist items."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.dependencies import CurrentUserDep, WishlistServiceDep
from app.schemas.wishlist_schema import (
    WishlistActionRead,
    WishlistCreate,
    WishlistRead,
    WishlistStatsRead,
)

wishlist_route = APIRouter(prefix="/api/v1/wishlist", tags=["Wishlist"])


@wishlist_route.get(
    "/",
    summary="Get user's wishlist",
    response_model=WishlistRead,
)
async def get_wishlist(
    current_user: CurrentUserDep, wishlist_service: WishlistServiceDep
) -> WishlistRead:
    """Get the wishlist items for the current user."""
    return await wishlist_service.get_items(user_id=current_user.id)


@wishlist_route.post(
    "/",
    summary="Add product to wishlist",
    response_model=WishlistActionRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_product_to_wishlist(
    data: WishlistCreate, current_user: CurrentUserDep, wishlist_service: WishlistServiceDep
) -> WishlistActionRead:
    """Add a product to the user's wishlist."""
    return await wishlist_service.add_item(user_id=current_user.id, product_id=data.product_id)


@wishlist_route.delete(
    "/{product_id}/",
    summary="Remove product from wishlist",
    response_model=WishlistActionRead,
)
async def remove_product_from_wishlist(
    product_id: UUID,
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistActionRead:
    """Remove a product from the user's wishlist."""
    return await wishlist_service.remove_item(user_id=current_user.id, product_id=product_id)


@wishlist_route.delete(
    "/clear/",
    summary="Clear user's wishlist",
    response_model=WishlistActionRead,
)
async def clear_wishlist(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistActionRead:
    """Clear all items from the user's wishlist."""
    return await wishlist_service.clear(user_id=current_user.id)


@wishlist_route.get(
    "/count/",
    summary="Get count of wishlist items",
    response_model=WishlistStatsRead,
)
async def get_wishlist_count(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistStatsRead:
    """Get the count of items in the user's wishlist."""
    return await wishlist_service.get_count(user_id=current_user.id)


@wishlist_route.get(
    "/{product_id}/move-to-cart/",
    summary="Move product from wishlist to cart",
    response_model=WishlistActionRead,
)
async def move_product_to_cart(
    product_id: UUID,
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistActionRead:
    """Move a product from the user's wishlist to their cart."""
    return await wishlist_service.move_to_cart(user_id=current_user.id, product_id=product_id)
