"""Interface for User repository."""

from abc import ABC, abstractmethod

from app.interfaces.generic_repository import GenericRepository
from app.models.user import User


class UserRepository(GenericRepository[User], ABC):
    """Interface for User repository."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get a single user by email.

        Args:
            email (str): User email.

        Returns:
            User | None: User or none.
        """
        raise NotImplementedError()
