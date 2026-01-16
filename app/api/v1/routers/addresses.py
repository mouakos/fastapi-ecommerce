"""Address management API routes for user delivery and billing addresses."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.dependencies import AddressServiceDep, CurrentUserDep
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.get(
    "",
    response_model=list[AddressRead],
    summary="List user addresses",
    description="Retrieve all delivery and billing addresses associated with the current user.",
)
async def get_user_addresses(
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> list[AddressRead]:
    """List all addresses for the current user."""
    return await address_service.get_user_addresses(current_user.id)


@router.post(
    "",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add new address",
    description="Create a new delivery or billing address for the current user.",
)
async def add_user_address(
    data: AddressCreate,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> AddressRead:
    """Add a new address to the currently authenticated user's account."""
    return await address_service.add_user_address(current_user.id, data)


@router.patch(
    "/{address_id}",
    response_model=AddressRead,
    summary="Update address",
    description="Update an existing address. Only the address owner can modify it.",
)
async def update_user_address(
    address_id: UUID,
    data: AddressUpdate,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> AddressRead:
    """Update an existing address. Only the owner can update their own address."""
    return await address_service.update_user_address(address_id, current_user.id, data)


@router.patch(
    "/{address_id}/default-shipping",
    response_model=AddressRead,
    summary="Set address as default shipping",
    description="Mark an address as the default shipping address for the user.",
)
async def set_user_default_shipping_address(
    address_id: UUID,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> AddressRead:
    """Set an address as the default shipping address for the current user."""
    return await address_service.set_user_default_shipping_address(address_id, current_user.id)


@router.patch(
    "/{address_id}/default-billing",
    response_model=AddressRead,
    summary="Set address as default billing",
    description="Mark an address as the default billing address for the user.",
)
async def set_user_default_billing_address(
    address_id: UUID,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> AddressRead:
    """Set an address as the default billing address for the current user."""
    return await address_service.set_user_default_billing_address(address_id, current_user.id)


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user address",
    description="Remove an address from the user's account.",
)
async def delete_user_address(
    address_id: UUID,
    current_user: CurrentUserDep,
    address_service: AddressServiceDep,
) -> None:
    """Delete an existing address. Only the owner or an admin can delete an address."""
    await address_service.delete_user_address(address_id, current_user.id)
