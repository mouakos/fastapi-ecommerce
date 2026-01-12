"""User API Routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.v1.dependencies import (
    AddressServiceDep,
    CurrentUserDep,
    UserServiceDep,
)
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently authenticated user's profile.",
)
async def get_user(
    current_user: CurrentUserDep,
) -> UserRead:
    """Retrieve the profile of the currently authenticated user."""
    return current_user


@router.put(
    "/me",
    response_model=UserRead,
    summary="Update the current user's profile.",
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
    summary="Delete the currently authenticated user's account.",
)
async def delete_user(
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> None:
    """Delete the current user's account."""
    await user_service.delete(current_user.id)


@router.get(
    "/me/addresses",
    response_model=list[AddressRead],
    summary="List all addresses for the current user.",
)
async def list_addresses(
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> list[AddressRead]:
    """List all addresses for the current user.."""
    return await address_service.list_all(current_user.id)


@router.post(
    "/me/addresses",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new address to the current user.",
)
async def add_address(
    data: AddressCreate,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> AddressRead:
    """Add a new address to the currently authenticated user's account."""
    return await address_service.create(current_user.id, data)


@router.put(
    "/me/addresses/{address_id}",
    response_model=AddressRead,
    summary="Update an existing address for the current user.",
)
async def update_address(
    address_id: UUID,
    data: AddressUpdate,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> AddressRead:
    """Update an existing address for the currently authenticated user's account."""
    address = await address_service.get_by_id(address_id)
    if address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough permissions to perform this action.",
        )
    return await address_service.update(address_id, data)


@router.delete(
    "/me/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an existing address for the current user.",
)
async def delete_address(
    address_id: UUID,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> None:
    """Delete an existing address for the currently authenticated user's account."""
    address = await address_service.get_by_id(address_id)
    if address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough permissions to perform this action.",
        )
    await address_service.delete(address_id)
