"""User authentication API routes for registration and login."""

# mypy: disable-error-code=return-value
from fastapi import APIRouter, status

from app.api.v1.dependencies import CartServiceDep, CartSessionIdDep, UserServiceDep
from app.schemas.user import Login, Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="Create a new user account with email and password. Email must be unique and password must meet security requirements.",
)
async def register(data: UserCreate, user_service: UserServiceDep) -> UserRead:
    """Register a new user."""
    return await user_service.create(data)


@router.post(
    "/login",
    response_model=Token,
    summary="Login user",
    description="Authenticate with email and password to receive a JWT access token. If a guest cart session exists, it will be merged with the user's cart.",
)
async def login(
    data: Login,
    session_id: CartSessionIdDep,
    user_service: UserServiceDep,
    cart_service: CartServiceDep,
) -> Token:
    """Authenticate user and return access token."""
    token, user = await user_service.login(data)
    if session_id:
        await cart_service.merge_carts(user.id, session_id)
    return token
