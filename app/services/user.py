"""Service layer for user-related operations."""

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import Login, Token, UserCreate


class UserService:
    """Service layer for user-related operations."""

    @staticmethod
    async def create(session: AsyncSession, data: UserCreate) -> User:
        """Create a new user.

        Args:
            session (AsyncSession): The database session.
            data (UserCreate): User data.

        Returns:
            User: The created user.

        Raises:
            HTTPException: If the user already exists.
        """
        stmt = select(User).where(User.email == str(data.email))
        user = (await session.exec(stmt)).first()

        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists."
            )

        hashed_password = hash_password(data.password)
        user_data = data.model_dump(exclude={"password"})

        new_user = User(hashed_password=hashed_password, **user_data)
        session.add(new_user)
        await session.flush()
        await session.refresh(new_user)
        return new_user

    @staticmethod
    async def login(session: AsyncSession, data: Login) -> Token:
        """Authenticate a user.

        Args:
            session (AsyncSession): The database session.
            data (Login): Login data.

        Returns:
            Token: Token data.

        Raises:
            HTTPException: If the password or email is invalid.
        """
        stmt = select(User).where(User.email == str(data.email))
        user = (await session.exec(stmt)).first()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password."
            )

        token = create_access_token({"sub": str(user.id)})
        return Token(access_token=token)
