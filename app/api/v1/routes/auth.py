"""Authentication API Routes."""

# mypy: disable-error-code=return-value

from fastapi import APIRouter, status

from app.api.v1.dependencies import SessionDep
from app.schemas.user import Login, Token, UserCreate, UserRead
from app.services.user import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account.",
)
async def create_user(data: UserCreate, session: SessionDep) -> UserRead:
    """Register a new user."""
    return await UserService.create(session, data)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate a user and return a JWT token.",
)
async def login(data: Login, session: SessionDep) -> Token:
    """Register a new user."""
    return await UserService.login(session, data)
