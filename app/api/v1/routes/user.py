"""User API Routes."""

# mypy: disable-error-code=return-value
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.database import get_session
from app.models.user import User
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate
from app.schemas.user import Login, Token, UserCreate, UserRead, UserUpdate
from app.services.address import AddressService
from app.services.user import UserService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account.",
)
async def create_user(
    data: UserCreate, session: Annotated[AsyncSession, Depends(get_session)]
) -> UserRead:
    """Register a new user."""
    return await UserService.create(session, data)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate a user and return a JWT token.",
)
async def login(data: Login, session: Annotated[AsyncSession, Depends(get_session)]) -> Token:
    """Register a new user."""
    return await UserService.login(session, data)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently authenticated user's profile.",
)
async def get_user(
    current_user: Annotated[User, Depends(get_current_user)],
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
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRead:
    """Update the profile of the currently authenticated user."""
    return await UserService.update(session, current_user.id, data)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete the currently authenticated user's account.",
)
async def delete_user(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete the current user's account."""
    await UserService.delete(session, current_user.id)


@router.get(
    "/me/addresses",
    response_model=list[AddressRead],
    summary="List all addresses for the current user.",
)
async def list_addresses(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
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
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
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
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
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
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete an existing address for the currently authenticated user's account."""
    address = await AddressService.get_by_id(session, address_id)
    if address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have enough permissions to perform this action.",
        )
    await AddressService.delete(session, address_id)
