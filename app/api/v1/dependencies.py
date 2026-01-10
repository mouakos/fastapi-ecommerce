"""API Routes dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import decode_access_token
from app.db.database import get_session
from app.models.user import User
from app.services.user import UserService

oauth_scheme = HTTPBearer(
    scheme_name="Bearer",
    auto_error=False,
    description="JWT Access Token in the Authorization header",
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
TokenDep = Annotated[HTTPAuthorizationCredentials, Depends(oauth_scheme)]


async def get_current_user(
    credentials: TokenDep,
    session: SessionDep,
) -> User:
    """Get current authenticated user from JWT token."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    decoded_token = decode_access_token(token=credentials.credentials)
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decoded_token.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await UserService.get_by_id(session, UUID(user_id))


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_current_user(
    credentials: TokenDep,
    session: SessionDep,
) -> User | None:
    """Get current authenticated user from JWT token, or None if not authenticated."""
    try:
        return await get_current_user(credentials, session)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise


OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]
