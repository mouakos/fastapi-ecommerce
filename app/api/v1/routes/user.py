"""User API Routes."""

# mypy: disable-error-code=return-value
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.database import get_session
from app.models.user import User
from app.schemas.user import Login, Token, UserCreate, UserRead, UserUpdate
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
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete the current user's account."""
    await UserService.delete(db, current_user.id)
