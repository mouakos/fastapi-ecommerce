"""Shopping cart management API routes for authenticated and guest users."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies import (
    CartServiceDep,
    CartSessionIdOrCreateDep,
    OptionalCurrentUserDep,
)
from app.schemas.cart import (
    AddToCartRequest,
    CartActionResponse,
    CartPublic,
    UpdateQuantityRequest,
)

router = APIRouter()


@router.get(
    "",
    response_model=CartPublic,
    summary="Get cart",
    description="Retrieve the current cart contents for authenticated users or session-based guests.",
)
async def get_cart(
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> CartPublic:
    """Get the current user's cart or session cart."""
    return await cart_service.get_cart(
        user_id=current_user.id if current_user else None, session_id=session_id
    )


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear cart",
    description="Remove all items from the cart. This action cannot be undone.",
)
async def clear_cart(
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> None:
    """Clear all items from the cart."""
    await cart_service.clear_cart(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
    )


@router.post(
    "/items",
    response_model=CartActionResponse,
    summary="Add product to cart",
    description="Add a product to the cart with the specified quantity. If the product already exists, the quantities will be combined.",
)
async def add_product_to_cart(
    data: AddToCartRequest,
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> CartActionResponse:
    """Add a product to the cart."""
    await cart_service.add_product_to_cart(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        product_id=data.product_id,
        quantity=data.quantity,
    )
    return CartActionResponse(
        message="Product added to cart successfully.", product_id=data.product_id
    )


@router.patch(
    "/items/{product_id}",
    response_model=CartActionResponse,
    summary="Update product quantity",
    description="Update the quantity of a specific product in the cart. Set quantity to 0 to remove the item.",
)
async def update_product_quantity(
    product_id: UUID,
    data: UpdateQuantityRequest,
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> CartActionResponse:
    """Update the quantity of a product in the cart."""
    await cart_service.update_product_quantity(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        product_id=product_id,
        quantity=data.quantity,
    )
    return CartActionResponse(
        message="Product updated in cart successfully.", product_id=product_id
    )


@router.delete(
    "/items/{product_id}",
    response_model=CartActionResponse,
    summary="Remove product from cart",
    description="Remove a specific product from the cart completely, regardless of quantity.",
)
async def remove_product_from_cart(
    product_id: UUID,
    session_id: CartSessionIdOrCreateDep,
    current_user: OptionalCurrentUserDep,
    cart_service: CartServiceDep,
) -> CartActionResponse:
    """Remove a product from the cart."""
    await cart_service.remove_product_from_cart(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        product_id=product_id,
    )
    return CartActionResponse(
        message="Product removed from cart successfully.", product_id=product_id
    )
