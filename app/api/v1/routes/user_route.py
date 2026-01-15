"""User API Routes."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.dependencies import (
    AddressServiceDep,
    CurrentUserDep,
    UserServiceDep,
)
from app.schemas.address_schema import AddressCreate, AddressRead, AddressUpdate
from app.schemas.user_schema import UserRead, UserUpdate

user_router = APIRouter(prefix="/users", tags=["Users"])


# Current user profile operations
@user_router.get(
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


@user_router.put(
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


@user_router.delete(
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


# Current user addresses operations
@user_router.get(
    "/me/addresses",
    response_model=list[AddressRead],
    summary="List user addresses",
    description="Retrieve all delivery and billing addresses associated with the current user.",
)
async def list_addresses(
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> list[AddressRead]:
    """List all addresses for the current user."""
    return await address_service.list_all(current_user)


@user_router.post(
    "/me/addresses",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add new address",
    description="Create a new delivery or billing address for the current user.",
)
async def add_address(
    data: AddressCreate,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> AddressRead:
    """Add a new address to the currently authenticated user's account."""
    return await address_service.create(current_user, data)


@user_router.put(
    "/me/addresses/{address_id}",
    response_model=AddressRead,
    summary="Update address",
    description="Update an existing address. Only the address owner can modify it.",
)
async def update_address(
    address_id: UUID,
    data: AddressUpdate,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> AddressRead:
    """Update an existing address. Only the owner can update their own address."""
    return await address_service.update(current_user, address_id, data)


@user_router.delete(
    "/me/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete address",
    description="Remove an address from the user's account. Only the owner or admin can delete addresses.",
)
async def delete_address(
    address_id: UUID,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> None:
    """Delete an existing address. Only the owner or an admin can delete an address."""
    await address_service.delete(current_user, address_id)
