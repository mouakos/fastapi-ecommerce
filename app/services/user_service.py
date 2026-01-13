"""Service layer for user-related operations."""

# mypy: disable-error-code=return-value
from uuid import UUID

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.interfaces.unit_of_work import UnitOfWork
from app.models.user import User
from app.schemas.user_schema import Login, Token, UserCreate, UserRead, UserUpdate


class UserService:
    """Service layer for user-related operations."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the service with a unit of work."""
        self.uow = uow

    async def get_by_id(self, user_id: UUID) -> UserRead:
        """Fetch a user by id.

        Args:
            user_id (UUID): User ID.

        Returns:
            UserRead: The user with the specified ID.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    async def create(self, data: UserCreate) -> UserRead:
        """Create a new user.

        Args:
            data (UserCreate): User data.

        Returns:
            UserRead: The created user.

        Raises:
            HTTPException: If the user already exists.
        """
        user = await self.uow.users.get_by_email(data.email)

        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists."
            )

        hashed_password = hash_password(data.password)
        user_data = data.model_dump(exclude={"password"})

        new_user = User(hashed_password=hashed_password, **user_data)

        return await self.uow.users.add(new_user)

    async def login(self, data: Login) -> tuple[Token, UserRead]:
        """Authenticate a user.

        Args:
            data (Login): Login data.

        Returns:
            Token: Token data.

        Raises:
            HTTPException: If the password or email is invalid.
        """
        user = await self.uow.users.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password."
            )

        token = create_access_token({"sub": str(user.id)})
        return Token(access_token=token), user

    async def update(self, user_id: UUID, data: UserUpdate) -> UserRead:
        """Update mutable profile fields (first/last name, phone number).

        Args:
            user_id (UUID): User ID.
            data (UserUpdate): User data.

        Returns:
            UserRead: The updated user.

        Raises:
            HTTPException: If the user does not exist.
        """
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        user_data = data.model_dump(exclude_unset=True)
        for key, value in user_data.items():
            setattr(user, key, value)

        return await self.uow.users.update(user)

    async def delete(self, user_id: UUID) -> None:
        """Delete user.

        Args:
            user_id (UUID): User ID.

        Raises:
            HTTPException: If the user does not exist.
        """
        if not await self.uow.users.delete_by_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
