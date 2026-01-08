"""User API Routes."""

# mypy: disable-error-code=return-value
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_session
from app.schemas.user import Login, Token, UserCreate, UserRead
from app.services.user import UserService

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserRead,
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
