"""User profile management API routes for authenticated users."""

from fastapi import APIRouter, status

from app.api.v1.dependencies import (
    CurrentUserDep,
    UserServiceDep,
)
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


# Current user profile operations
@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
    description="Retrieve the profile information of the currently authenticated user.",
)
async def get_user(
    current_user: CurrentUserDep,
) -> UserRead:
    """Retrieve the profile of the currently authenticated user."""
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user profile",
    description="Update profile information such as name, email, or other personal details.",
)
async def update_user(
    data: UserUpdate,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> UserRead:
    """Update the profile of the currently authenticated user."""
    return await user_service.update(current_user.id, data)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
    description="Permanently delete the current user's account. This action cannot be undone.",
)
async def delete_user(
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> None:
    """Delete the current user's account."""
    await user_service.delete(current_user.id)
