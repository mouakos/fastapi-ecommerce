"""Wishlist management API routes for saving and organizing favorite products."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import CurrentUserDep, WishlistServiceDep
from app.schemas.common import Page
from app.schemas.wishlist import (
    WishlistCreate,
    WishlistItemRead,
    WishlistStatsRead,
)
from app.utils.pagination import build_page

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.get(
    "/count",
    summary="Get wishlist item count",
    description="Retrieve the total number of products currently saved in the user's wishlist.",
    response_model=WishlistStatsRead,
)
async def get_wishlist_item_count(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistStatsRead:
    """Get the count of items in the user's wishlist."""
    count = await wishlist_service.get_wishlist_item_count(user_id=current_user.id)
    return WishlistStatsRead(count=count)


@router.get(
    "",
    summary="List wishlist items",
    description="Retrieve paginated list of all products in the user's wishlist with product details including price, stock, and availability.",
    response_model=Page[WishlistItemRead],
)
async def get_wishlist_items(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
) -> Page[WishlistItemRead]:
    """Get the wishlist items for the current user."""
    wishlist_items, total = await wishlist_service.get_wishlist_items(
        user_id=current_user.id, page=page, page_size=page_size
    )
    items = []
    if wishlist_items:
        for item in wishlist_items:
            items.append(
                WishlistItemRead(
                    id=item.id,
                    product_id=item.product.id,
                    product_name=item.product.name,
                    product_slug=item.product.slug,
                    product_price=item.product.price,
                    product_image_url=item.product.image_url,
                    product_stock_quantity=item.product.stock,
                    product_is_active=item.product.is_active,
                    added_at=item.created_at,
                )
            )

    return build_page(items=items, page=page, size=page_size, total=total)


@router.post(
    "",
    summary="Add product to wishlist",
    description="Add a product to wishlist. If the product is already in the wishlist, this operation has no effect.",
    status_code=status.HTTP_201_CREATED,
)
async def add_wishlist_item(
    data: WishlistCreate, current_user: CurrentUserDep, wishlist_service: WishlistServiceDep
) -> None:
    """Add a product to the user's wishlist."""
    await wishlist_service.add_wishlist_item(user_id=current_user.id, product_id=data.product_id)


@router.delete(
    "",
    summary="Clear wishlist",
    description="Remove all items from wishlist. This action cannot be undone.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_wishlist_items(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> None:
    """Clear all items from the user's wishlist."""
    await wishlist_service.clear_wishlist_items(user_id=current_user.id)


@router.delete(
    "/{product_id}",
    summary="Remove product from wishlist",
    description="Remove a specific product from wishlist by its ID.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_wishlist_item(
    product_id: UUID,
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> None:
    """Remove a product from the user's wishlist."""
    await wishlist_service.remove_wishlist_item(user_id=current_user.id, product_id=product_id)


@router.post(
    "/{product_id}/move-to-cart",
    summary="Move product to cart",
    description="Remove product from wishlist and add it to shopping cart with default quantity of 1.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def move_wishlist_item_to_cart(
    product_id: UUID,
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> None:
    """Move a product from the user's wishlist to their cart."""
    await wishlist_service.move_wishlist_item_to_cart(
        user_id=current_user.id, product_id=product_id
    )
