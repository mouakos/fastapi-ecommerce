"""Address management API routes for user delivery and billing addresses."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.dependencies import AddressServiceDep, CurrentUserDep
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate

router = APIRouter(prefix="/users/me/addresses", tags=["Addresses"])


@router.get(
    "",
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


@router.post(
    "",
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


@router.patch(
    "/{address_id}",
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


@router.delete(
    "/{address_id}",
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
