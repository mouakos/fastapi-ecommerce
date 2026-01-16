"""Interface for User repository."""

from abc import ABC, abstractmethod
from typing import Any

from app.interfaces.generic_repository import GenericRepository
from app.models.user import User, UserRole


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
        ...

    @abstractmethod
    async def count_all(self, **filters: Any) -> int:  # noqa: ANN401
        """Get total number of users.

        Args:
            **filters: Filter conditions.

        Returns:
            int: Total number of users.

        Raises:
            ValueError: If invalid filters are provided.
        """
        ...

    @abstractmethod
    async def count_recent_users(self, days: int) -> int:
        """Get number of users registered in the last N days.

        Args:
            days (int): Number of days to look back from today.

        Returns:
            int: Number of users registered in the last N days.
        """
        ...

    @abstractmethod
    async def get_all_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        role: UserRole | None = None,
        search: str | None = None,
    ) -> tuple[int, list[User]]:
        """Get all users with pagination and optional filters.

        Args:
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 100.
            role (UserRole | None, optional): Filter by user role. Defaults to None.
            search (str | None, optional): Search query for name or email. Defaults to None.

        Returns:
            tuple[int, list[User]]: Total count and list of users.
        """
        ...
