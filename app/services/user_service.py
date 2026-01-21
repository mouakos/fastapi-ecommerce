"""Service layer for user-related operations."""

from uuid import UUID

from app.core.exceptions import (
    DuplicateResourceError,
    IncorrectPasswordError,
    InvalidCredentialsError,
    PasswordMismatchError,
    UserNotFoundError,
)
from app.core.logger import logger
from app.core.security import create_access_token, hash_password, verify_password
from app.interfaces.unit_of_work import UnitOfWork
from app.models.user import User
from app.schemas.user import Login, Token, UserCreate, UserPasswordUpdate, UserUpdate


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
            UserNotFoundError: If the user does not exist.
        """
        user = await self.uow.users.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user.

        Args:
            data (UserCreate): User data.

        Returns:
            User: The created user.

        Raises:
            DuplicateResourceError: If a user with this email already exists.
        """
        user = await self.uow.users.find_by_email(data.email)

        if user:
            raise DuplicateResourceError(
                resource="User",
                field="email",
                value=data.email,
            )

        hashed_password = hash_password(data.password)
        user_data = data.model_dump(exclude={"password"})

        new_user = User(hashed_password=hashed_password, **user_data)
        created_user = await self.uow.users.add(new_user)
        logger.info("user_registered", user_id=str(created_user.id), email=created_user.email)
        return created_user

    async def login(self, data: Login) -> tuple[Token, User]:
        """Authenticate a user and generate JWT access token.

        Args:
            data (Login): Login credentials (email and password).

        Returns:
            tuple[Token, User]: JWT access token and authenticated user object.

        Raises:
            InvalidCredentialsError: If email or password is incorrect.
        """
        user = await self.uow.users.find_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError()

        token = create_access_token({"sub": str(user.id)})
        logger.info("user_logged_in", user_id=str(user.id), email=user.email)
        return Token(access_token=token), user

    async def update_user_password(self, user_id: UUID, data: UserPasswordUpdate) -> None:
        """Update user password with verification of current password.

        Args:
            user_id (UUID): ID of the user.
            data (UserPasswordUpdate): Old password, new password, and confirmation.

        Raises:
            UserNotFoundError: If user not found.
            IncorrectPasswordError: If old password is incorrect.
            PasswordMismatchError: If new password and confirmation do not match.
        """
        user = await self.get_user(user_id)

        if not verify_password(data.old_password, user.hashed_password):
            raise IncorrectPasswordError()

        if data.new_password != data.confirm_password:
            raise PasswordMismatchError()

        user.hashed_password = hash_password(data.new_password)
        await self.uow.users.update(user)
        logger.info("user_password_updated", user_id=str(user_id))

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """Update user information.

        Args:
            user_id (UUID): User ID.
            data (UserUpdate): User data.

        Returns:
            User: The updated user.

        Raises:
            UserNotFoundError: If the user does not exist.
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
            UserNotFoundError: If the user does not exist.
        """
        user = await self.get_user(user_id)
        await self.uow.users.delete(user)
        logger.info("user_deleted", user_id=str(user_id))
