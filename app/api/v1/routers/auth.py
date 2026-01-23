"""User authentication API routes for registration and login."""

# mypy: disable-error-code=return-value
from fastapi import APIRouter, Depends, status

from app.api.jwt_bearer import revoke_token
from app.api.rate_limit import rate_limit
from app.api.v1.dependencies import (
    CartServiceDep,
    CartSessionIdDep,
    RefreshTokenDep,
    UserServiceDep,
)
from app.core.config import auth_settings
from app.core.security import create_access_token, create_refresh_token
from app.schemas.user import Login, Token, UserActionResponse, UserCreate, UserPublic

router = APIRouter()


@router.post(
    "/sign-up",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="Create a new user account with email and password. Email must be unique and password must meet security requirements.",
)
async def register(data: UserCreate, user_service: UserServiceDep) -> UserPublic:
    """Register a new user."""
    return await user_service.create_user(data)


@router.post(
    "/access-token",
    dependencies=[Depends(rate_limit(times=5, seconds=60))],
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

    payload = {"sub": str(user.id)}
    expired_in = auth_settings.jwt_access_token_exp_minutes * 60  # in seconds

    return Token(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
        expires_in=expired_in,
    )


@router.get(
    "/refresh-token",
    response_model=Token,
    summary="Refresh access token",
    description="Generate a new access token and refresh token using a valid refresh token. The old refresh token will be revoked.",
)
async def get_new_access_token(
    token_data: RefreshTokenDep,
) -> Token:
    """Generate a new access token using a valid refresh token."""
    # Create new access and refresh tokens
    payload = {"sub": str(token_data.user_id)}
    new_access_token = create_access_token(payload)
    new_refresh_token = create_refresh_token(payload)

    # Revoke the old refresh token
    await revoke_token(token_data.jti)

    expired_in = auth_settings.jwt_access_token_exp_minutes * 60  # in seconds
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=expired_in,
    )


@router.post(
    "/logout",
    summary="Revoke refresh token",
    description="Revoke a refresh token to prevent further use.",
)
async def revoke_refresh_token(
    token_data: RefreshTokenDep,
) -> UserActionResponse:
    """Revoke a refresh token to prevent further use."""
    await revoke_token(token_data.jti)
    return UserActionResponse(message="Logout successful.", user_id=token_data.user_id)
