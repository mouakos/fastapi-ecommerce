"""Service layer for user-related operations."""

from uuid import UUID

from app.core.exceptions import (
    DuplicateUserError,
    InactiveUserError,
    IncorrectPasswordError,
    InvalidCredentialsError,
    PasswordMismatchError,
    UserNotFoundError,
)
from app.core.logger import logger
from app.core.security import hash_password, verify_password
from app.interfaces.unit_of_work import UnitOfWork
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserPasswordUpdateRequest,
    UserUpdate,
)
from app.utils.datetime import utcnow


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
            raise UserNotFoundError(user_id=user_id)
        return user

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user.

        Args:
            data (UserCreate): User data.

        Returns:
            User: The created user.

        Raises:
            DuplicateUserError: If a user with this email already exists.
        """
        email = data.email.lower().strip()
        user = await self.uow.users.find_by_email(email)

        if user:
            raise DuplicateUserError(email=data.email)
        hashed_password = hash_password(data.password)
        user_data = data.model_dump(exclude={"password", "email"})

        new_user = User(hashed_password=hashed_password, email=email, **user_data)

        created_user = await self.uow.users.add(new_user)

        logger.info("user_registered", user_id=str(created_user.id), email=created_user.email)
        return created_user

    async def authenticate_user(self, *, email: str, password: str) -> User:
        """Authenticate a user and generate JWT access token.

        Args:
            email (str): User email.
            password (str): User password.

        Returns:
            User: Authenticated user object.

        Raises:
            InvalidCredentialsError: If email or password is incorrect.
            InactiveUserError: If the user account is inactive.
        """
        email = email.lower().strip()
        user = await self.uow.users.find_by_email(email)
        if (
            not user
            or not verify_password(password, user.hashed_password)
            or user.deleted_at is not None
        ):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError(user_id=user.id)

        user.last_login = utcnow()
        await self.uow.users.update(user)

        logger.info("user_logged_in", user_id=str(user.id), email=user.email)

        return user

    async def update_user_password(self, user_id: UUID, data: UserPasswordUpdateRequest) -> None:
        """Update user password with verification of current password.

        Args:
            user_id (UUID): ID of the user.
            data (UserPasswordUpdateRequest): Old password, new password, and confirmation.

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

        user = await self.uow.users.update(user)
        logger.info("user_updated", user_id=str(user_id))
        return user

    async def delete_user(self, user_id: UUID) -> None:
        """Deactivate a user account and anonymize PII.

        Args:
            user_id (UUID): User ID.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        user = await self.get_user(user_id)

        # Idempotent: if already deactivated, do nothing.
        if not user.is_active and user.deleted_at is not None:
            return

        # Remove addresses (PII). Orders keep snapshots in order_addresses.
        for address in list(user.addresses):
            await self.uow.addresses.delete(address)

        # Remove carts (non-essential).
        cart = await self.uow.carts.find_user_cart(user.id)
        if cart:
            await self.uow.carts.delete(cart)

        # Deactivate + anonymize core PII.
        user.is_active = False
        user.first_name = None
        user.last_name = None
        user.phone_number = None
        user.email = f"deleted+{user.id}@example.com"
        user.hashed_password = hash_password(f"deleted:{user.id}:{utcnow().isoformat()}")
        user.deleted_at = utcnow()

        await self.uow.users.update(user)
        logger.info("user_deactivated", user_id=str(user_id))
