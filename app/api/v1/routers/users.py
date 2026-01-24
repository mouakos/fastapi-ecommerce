"""User profile management API routes for authenticated users."""

# mypy: disable-error-code=return-value
from fastapi import APIRouter, status

from app.api.jwt_bearer import revoke_token
from app.api.v1.dependencies import (
    AccessTokenDep,
    CurrentUserDep,
    RefreshTokenDep,
    UserServiceDep,
)
from app.schemas.user import (
    UserActionResponse,
    UserPasswordUpdateRequest,
    UserPublic,
    UserUpdate,
)

router = APIRouter()


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user profile",
    description="Retrieve the profile information of the currently authenticated user.",
)
async def get_user(
    current_user: CurrentUserDep,
) -> UserPublic:
    """Retrieve the profile of the currently authenticated user."""
    return current_user


@router.patch(
    "/me",
    response_model=UserPublic,
    summary="Update current user profile",
    description="Update profile information such as name, email, or other personal details.",
)
async def update_user(
    data: UserUpdate,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> UserPublic:
    """Update the profile of the currently authenticated user."""
    return await user_service.update_user(current_user.id, data)


@router.patch(
    "/me/password",
    summary="Change current user password",
    description="Update the password of the currently authenticated user. Requires the old password for verification.",
)
async def change_user_password(
    data: UserPasswordUpdateRequest,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
    token_data: AccessTokenDep,
) -> UserActionResponse:
    """Change the password of the currently authenticated user."""
    await user_service.update_user_password(current_user.id, data)

    # Revoke all tokens associated with the user
    await revoke_token(token_data.jti, token_data.exp)

    return UserActionResponse(message="Password updated successfully.", user_id=current_user.id)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
    description="Permanently delete the current user's account. This action cannot be undone.",
)
async def delete_user(
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
    token_data: RefreshTokenDep,  # TODO: Should this be AccessTokenDep?
) -> None:
    """Delete the current user's account."""
    await user_service.delete_user(current_user.id)

    # Revoke all tokens associated with the user
    await revoke_token(token_data.jti, token_data.exp)
