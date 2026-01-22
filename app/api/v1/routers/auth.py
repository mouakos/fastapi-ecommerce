"""User authentication API routes for registration and login."""

# mypy: disable-error-code=return-value
from fastapi import APIRouter, status

from app.api.v1.dependencies import CartServiceDep, CartSessionIdDep, UserServiceDep
from app.core.security import create_access_token
from app.schemas.user import Login, Token, UserCreate, UserPublic

router = APIRouter()


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="Create a new user account with email and password. Email must be unique and password must meet security requirements.",
)
async def register(data: UserCreate, user_service: UserServiceDep) -> UserPublic:
    """Register a new user."""
    return await user_service.create_user(data)


@router.post(
    "/token",
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
    user = await user_service.authenticate_user(email=data.email, password=data.password)
    if session_id:
        await cart_service.merge_carts(user.id, session_id)
    return Token(access_token=create_access_token({"sub": str(user.id)}))
