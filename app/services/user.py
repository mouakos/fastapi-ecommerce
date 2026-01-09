"""Service layer for user-related operations."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import Login, Token, UserCreate, UserUpdate


class UserService:
    """Service layer for user-related operations."""

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: UUID) -> User:
        """Fetch a user by id.

        Args:
            session (AsyncSession): Database session.
            user_id (UUID): User ID.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

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
        await session.commit()
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

    @staticmethod
    async def update(session: AsyncSession, user_id: UUID, data: UserUpdate) -> User:
        """Update mutable profile fields (first/last name, phone number).

        Args:
            session (AsyncSession): Database session.
            user_id (UUID): User ID.
            data (UserUpdate): User data.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await UserService.get_by_id(session, user_id)
        user_data = data.model_dump(exclude_unset=True)
        for key, value in user_data.items():
            setattr(user, key, value)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID) -> None:
        """Delete user.

        Args:
            session (AsyncSession): Database session.
            user_id (UUID): User ID.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await UserService.get_by_id(session, user_id)
        await session.delete(user)
        await session.commit()
