"""Wishlist management API routes for saving and organizing favorite products."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.v1.dependencies import CurrentUserDep, WishlistServiceDep
from app.schemas.common import Page
from app.schemas.wishlist import (
    AddToWishlistRequest,
    WishlistActionResponse,
    WishlistItemPublic,
    WishlistStatsResponse,
)
from app.utils.pagination import build_page

router = APIRouter()


@router.get(
    "/count",
    summary="Get wishlist item count",
    description="Retrieve the total number of products currently saved in the user's wishlist.",
    response_model=WishlistStatsResponse,
)
async def get_wishlist_item_count(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistStatsResponse:
    """Get the count of items in the user's wishlist."""
    count = await wishlist_service.get_wishlist_item_count(user_id=current_user.id)
    return WishlistStatsResponse(count=count)


@router.get(
    "",
    summary="List wishlist items",
    description="Retrieve paginated list of all products in the user's wishlist with product details including price, stock, and availability.",
    response_model=Page[WishlistItemPublic],
)
async def get_wishlist_items(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
) -> Page[WishlistItemPublic]:
    """Get the wishlist items for the current user."""
    wishlist_items, total = await wishlist_service.get_wishlist_items(
        user_id=current_user.id, page=page, page_size=page_size
    )
    items = []
    if wishlist_items:
        for item in wishlist_items:
            items.append(
                WishlistItemPublic(
                    id=item.id,
                    product_id=item.product.id,
                    product_name=item.product.name,
                    product_slug=item.product.slug,
                    product_price=item.product.price,
                    product_image_url=item.product.image_url,
                    product_in_stock=item.product.stock > 0,
                    product_is_active=item.product.is_active,
                    added_at=item.created_at,
                )
            )

    return build_page(items=items, page=page, size=page_size, total=total)


@router.post(
    "",
    summary="Add product to wishlist",
    description="Add a product to wishlist.",
    response_model=WishlistActionResponse,
)
async def add_product_to_wishlist(
    data: AddToWishlistRequest, current_user: CurrentUserDep, wishlist_service: WishlistServiceDep
) -> WishlistActionResponse:
    """Add a product to the user's wishlist."""
    await wishlist_service.add_product_to_wishlist(
        user_id=current_user.id, product_id=data.product_id
    )
    return WishlistActionResponse(
        message="Product added to wishlist successfully.", product_id=data.product_id
    )


@router.delete(
    "",
    summary="Clear wishlist",
    description="Remove all items from wishlist. This action cannot be undone.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_wishlist(
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> None:
    """Clear all items from the user's wishlist."""
    await wishlist_service.clear_wishlist(user_id=current_user.id)


@router.delete(
    "/{product_id}",
    summary="Remove product from wishlist",
    description="Remove a specific product from wishlist by its ID.",
    response_model=WishlistActionResponse,
)
async def remove_product_from_wishlist(
    product_id: UUID,
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistActionResponse:
    """Remove a product from the user's wishlist."""
    await wishlist_service.remove_product_from_wishlist(
        user_id=current_user.id, product_id=product_id
    )
    return WishlistActionResponse(
        message="Product removed from wishlist successfully.", product_id=product_id
    )


@router.post(
    "/{product_id}/add-to-cart",
    summary="Add product to cart",
    description="Add a product from wishlist to cart with default quantity of 1.",
    response_model=WishlistActionResponse,
)
async def add_product_from_wishlist_to_cart(
    product_id: UUID,
    current_user: CurrentUserDep,
    wishlist_service: WishlistServiceDep,
) -> WishlistActionResponse:
    """Add a product from the user's wishlist to their cart."""
    await wishlist_service.add_product_from_wishlist_to_cart(
        user_id=current_user.id, product_id=product_id
    )
    return WishlistActionResponse(
        message="Product added to cart successfully.", product_id=product_id
    )
