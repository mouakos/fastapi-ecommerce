"""Service layer for user-related operations."""

from uuid import UUID

from fastapi import HTTPException, status

from app.core.logging import logger
from app.core.security import create_access_token, hash_password, verify_password
from app.interfaces.unit_of_work import UnitOfWork
from app.models.user import User
from app.schemas.user import Login, Token, UserCreate, UserUpdate


class UserService:
    """Service layer for user-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def get_user(self, user_id: UUID) -> User:
        """Get a user by its ID.

        Args:
            user_id (UUID): User ID.

        Returns:
            User: The user with the specified ID.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await self.uow.users.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user.

        Args:
            data (UserCreate): User data.

        Returns:
            User: The created user.

        Raises:
            HTTPException: If the user already exists.
        """
        user = await self.uow.users.find_by_email(data.email)

        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists."
            )

        hashed_password = hash_password(data.password)
        user_data = data.model_dump(exclude={"password"})

        new_user = User(hashed_password=hashed_password, **user_data)

        logger.info(f"Creating new user with email: {data.email}")

        return await self.uow.users.add(new_user)

    async def login(self, data: Login) -> tuple[Token, User]:
        """Authenticate a user and generate JWT access token.

        Args:
            data (Login): Login credentials (email and password).

        Returns:
            tuple[Token, User]: JWT access token and authenticated user object.

        Raises:
            HTTPException: If email or password is incorrect.
        """
        user = await self.uow.users.find_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password."
            )

        token = create_access_token({"sub": str(user.id)})
        return Token(access_token=token), user

    async def update_user_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> None:
        """Update user password with verification of current password.

        Args:
            user_id (UUID): ID of the user.
            old_password (str): Current password for verification.
            new_password (str): New password to set (will be hashed).

        Raises:
            HTTPException: If user not found or old password is incorrect.
        """
        user = await self.get_user(user_id)

        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Password mismatch."
            )

        user.hashed_password = hash_password(new_password)
        await self.uow.users.update(user)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """Update user information.

        Args:
            user_id (UUID): User ID.
            data (UserUpdate): User data.

        Returns:
            User: The updated user.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await self.get_user(user_id)

        user_data = data.model_dump(exclude_unset=True)
        for key, value in user_data.items():
            setattr(user, key, value)

        return await self.uow.users.update(user)

    async def delete_user(self, user_id: UUID) -> None:
        """Delete a user by its ID.

        Args:
            user_id (UUID): User ID.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await self.get_user(user_id)
        await self.uow.users.delete(user)
