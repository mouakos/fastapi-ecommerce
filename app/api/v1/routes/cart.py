"""API routes for cart operations."""
# mypy: disable-error-code=return-value

from uuid import UUID, uuid4

from fastapi import APIRouter, Request, Response

from app.api.v1.dependencies import OptionalCurrentUser, SessionDep
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead
from app.services.cart import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])

CART_SESSION_COOKIE = "cart_session_id"
CART_SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def get_or_create_session_id(request: Request, response: Response) -> str:
    """Get or create a cart session ID."""
    session_id = request.cookies.get(CART_SESSION_COOKIE)
    if not session_id:
        session_id = str(uuid4())
        response.set_cookie(
            key=CART_SESSION_COOKIE,
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=CART_SESSION_MAX_AGE,
        )
    return session_id


@router.get("/", response_model=CartRead, summary="Get current user's cart or session cart")
async def get_cart(
    request: Request,
    response: Response,
    current_user: OptionalCurrentUser,
    session: SessionDep,
) -> CartRead:
    """Get the current user's cart or session cart."""
    session_id = get_or_create_session_id(request, response)

    return await CartService.get_or_create_cart(
        session,
        user_id=current_user.id if current_user else None,
        session_id=session_id,
    )


@router.post("/items/", response_model=CartRead, summary="Add item to cart")
async def add_item(
    request: Request,
    response: Response,
    data: CartItemCreate,
    current_user: OptionalCurrentUser,
    session: SessionDep,
) -> CartRead:
    """Add an item to the cart."""
    session_id = get_or_create_session_id(request, response)

    return await CartService.add_item(
        session,
        data,
        user_id=current_user.id if current_user else None,
        session_id=session_id,
    )


@router.put("/items/{product_id}/", response_model=CartRead, summary="Update cart item quantity")
async def update_item(
    request: Request,
    response: Response,
    product_id: UUID,
    data: CartItemUpdate,
    current_user: OptionalCurrentUser,
    session: SessionDep,
) -> CartRead:
    """Update the quantity of a cart item."""
    session_id = get_or_create_session_id(request, response)

    return await CartService.update_item(
        session,
        product_id,
        data,
        user_id=current_user.id if current_user else None,
        session_id=session_id,
    )


@router.delete("/items/{product_id}/", response_model=CartRead, summary="Remove item from cart")
async def remove_item(
    request: Request,
    response: Response,
    product_id: UUID,
    current_user: OptionalCurrentUser,
    session: SessionDep,
) -> CartRead:
    """Remove an item from the cart."""
    session_id = get_or_create_session_id(request, response)

    return await CartService.remove_item(
        session,
        product_id=product_id,
        session_id=session_id,
        user_id=current_user.id if current_user else None,
    )
