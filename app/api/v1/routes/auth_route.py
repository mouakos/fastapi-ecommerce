"""Authentication API Routes."""

from fastapi import APIRouter, status

from app.api.v1.dependencies import CartServiceDep, CartSessionIdDep, UserServiceDep
from app.schemas.user_schema import Login, Token, UserCreate, UserRead

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account.",
)
async def create_user(data: UserCreate, user_service: UserServiceDep) -> UserRead:
    """Register a new user."""
    return await user_service.create(data)


@auth_router.post(
    "/login",
    response_model=Token,
    summary="Authenticate a user and return a JWT token.",
)
async def login(
    data: Login,
    session_id: CartSessionIdDep,
    user_service: UserServiceDep,
    cart_service: CartServiceDep,
) -> Token:
    """Register a new user."""
    token, user = await user_service.login(data)
    if session_id:
        await cart_service.merge_carts(user.id, session_id)
    return token
