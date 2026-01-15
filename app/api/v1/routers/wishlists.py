"""Wishlist management API routes for saving and organizing favorite products."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.dependencies import CurrentUserDep, WishlistServiceDep
from app.schemas.wishlist import (
    WishlistActionRead,
    WishlistCreate,
    WishlistRead,
    WishlistStatsRead,
)

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


# Static paths first
@router.get(
    "/count",
    summary="Get wishlist item count",
    description="Retrieve the total number of items currently in wishlist.",
    response_model=WishlistStatsRead,
)
async def get_wishlist_count(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistStatsRead:
    """Get the count of items in the user's wishlist."""
    return await wishlist_service.get_count(user_id=current_user.id)


# Root paths (collection operations)
@router.get(
    "",
    summary="Get user's wishlist",
    description="Retrieve all items in the current user's wishlist.",
    response_model=WishlistRead,
)
async def get_wishlist(
    current_user: CurrentUserDep, wishlist_service: WishlistServiceDep
) -> WishlistRead:
    """Get the wishlist items for the current user."""
    return await wishlist_service.get_items(user_id=current_user.id)


@router.post(
    "",
    summary="Add product to wishlist",
    description="Add a product to wishlist. If the product is already in the wishlist, this operation has no effect.",
    response_model=WishlistActionRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_product_to_wishlist(
    data: WishlistCreate, current_user: CurrentUserDep, wishlist_service: WishlistServiceDep
) -> WishlistActionRead:
    """Add a product to the user's wishlist."""
    return await wishlist_service.add_item(user_id=current_user.id, product_id=data.product_id)


@router.delete(
    "",
    summary="Clear wishlist",
    description="Remove all items from wishlist. This action cannot be undone.",
    response_model=WishlistActionRead,
)
async def clear_wishlist(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistActionRead:
    """Clear all items from the user's wishlist."""
    return await wishlist_service.clear(user_id=current_user.id)


# Parameterized paths last
@router.delete(
    "/{product_id}",
    summary="Remove product from wishlist",
    description="Remove a specific product from wishlist by its ID.",
    response_model=WishlistActionRead,
)
async def remove_product_from_wishlist(
    product_id: UUID,
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistActionRead:
    """Remove a product from the user's wishlist."""
    return await wishlist_service.remove_item(user_id=current_user.id, product_id=product_id)


@router.post(
    "/{product_id}/move-to-cart",
    summary="Move product to cart",
    description="Remove product from wishlist and add it to shopping cart with default quantity of 1.",
    response_model=WishlistActionRead,
)
async def move_product_to_cart(
    product_id: UUID,
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistActionRead:
    """Move a product from the user's wishlist to their cart."""
    return await wishlist_service.move_to_cart(user_id=current_user.id, product_id=product_id)
