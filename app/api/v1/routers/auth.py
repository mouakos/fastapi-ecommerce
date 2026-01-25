"""User authentication API routes for registration and login."""

# mypy: disable-error-code=return-value

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import (
    AccessTokenDataDep,
    CartServiceDep,
    CartSessionIdDep,
    RefreshTokenDataDep,
    RequestFormDep,
    UserServiceDep,
)
from app.api.rate_limit import rate_limit
from app.core.config import auth_settings
from app.core.security import create_access_token, create_refresh_token, revoke_token
from app.schemas.auth import Token
from app.schemas.user import UserActionResponse, UserCreate, UserPublic

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
    "/login",
    dependencies=[Depends(rate_limit(times=5, seconds=60))],
    response_model=Token,
    summary="Login user",
    description="Authenticate with email and password to receive a JWT access token. If a guest cart session exists, it will be merged with the user's cart.",
)
async def login(
    form_data: RequestFormDep,
    session_id: CartSessionIdDep,
    user_service: UserServiceDep,
    cart_service: CartServiceDep,
    response: Response,
) -> Token:
    """Authenticate user and return access token."""
    user = await user_service.authenticate_user(
        email=form_data.username, password=form_data.password
    )
    if session_id:
        await cart_service.merge_carts(user.id, session_id)

    payload = {"sub": str(user.id)}
    expired_in = auth_settings.jwt_access_token_exp_minutes * 60  # in seconds
    max_age = auth_settings.jwt_refresh_token_exp_days * 24 * 60 * 60
    response.set_cookie(
        key="refresh_token",
        value=create_refresh_token(payload),
        httponly=True,
        samesite="lax",
        max_age=max_age,
    )
    return Token(
        access_token=create_access_token(payload),
        expires_in=expired_in,
    )


@router.get(
    "/refresh-token",
    response_model=Token,
    summary="Refresh access token",
    description="Generate a new access token using a valid refresh token.",
)
async def get_new_access_token(
    refresh_token_data: RefreshTokenDataDep,
) -> Token:
    """Generate a new access token using a valid refresh token."""
    # Create new access token
    payload = {"sub": str(refresh_token_data.user_id)}
    new_access_token = create_access_token(payload)

    expired_in = auth_settings.jwt_access_token_exp_minutes * 60  # in seconds
    return Token(
        access_token=new_access_token,
        expires_in=expired_in,
    )


@router.post(
    "/logout",
    summary="Revoke refresh token",
    description="Revoke a refresh token to prevent further use.",
)
async def revoke_refresh_token(
    access_token_data: AccessTokenDataDep,
    refresh_token_data: RefreshTokenDataDep,
) -> UserActionResponse:
    """Revoke a refresh token to prevent further use."""
    # Revoke the refresh token
    await revoke_token(refresh_token_data.jti, refresh_token_data.exp)
    await revoke_token(access_token_data.jti, access_token_data.exp)
    return UserActionResponse(message="Logged out successfully.", user_id=access_token_data.user_id)
