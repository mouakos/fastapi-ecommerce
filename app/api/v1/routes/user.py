"""User API Routes."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.v1.dependencies import CurrentUser, SessionDep
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate
from app.schemas.user import UserRead, UserUpdate
from app.services.address import AddressService
from app.services.user import UserService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently authenticated user's profile.",
)
async def get_user(
    current_user: CurrentUser,
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
    current_user: CurrentUser,
    session: SessionDep,
) -> UserRead:
    """Update the profile of the currently authenticated user."""
    return await UserService.update(session, current_user.id, data)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete the currently authenticated user's account.",
)
async def delete_user(
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    """Delete the current user's account."""
    await UserService.delete(session, current_user.id)


@router.get(
    "/me/addresses",
    response_model=list[AddressRead],
    summary="List all addresses for the current user.",
)
async def list_addresses(
    current_user: CurrentUser,
    session: SessionDep,
) -> list[AddressRead]:
    """List all addresses for the current user.."""
    return await AddressService.list_all(session, current_user.id)


@router.post(
    "/me/addresses",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new address to the current user.",
)
async def add_address(
    data: AddressCreate,
    current_user: CurrentUser,
    session: SessionDep,
) -> AddressRead:
    """Add a new address to the currently authenticated user's account."""
    return await AddressService.create(session, data, current_user.id)


@router.put(
    "/me/addresses/{address_id}",
    response_model=AddressRead,
    summary="Update an existing address for the current user.",
)
async def update_address(
    address_id: UUID,
    data: AddressUpdate,
    current_user: CurrentUser,
    session: SessionDep,
) -> AddressRead:
    """Update an existing address for the currently authenticated user's account."""
    address = await AddressService.get_by_id(session, address_id)
    if address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough permissions to perform this action.",
        )
    return await AddressService.update(session, data, address_id)


@router.delete(
    "/me/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an existing address for the current user.",
)
async def delete_address(
    address_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> None:
    """Delete an existing address for the currently authenticated user's account."""
    address = await AddressService.get_by_id(session, address_id)
    if address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough permissions to perform this action.",
        )
    await AddressService.delete(session, address_id)
