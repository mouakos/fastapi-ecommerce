"""Interface for User repository."""

from abc import ABC, abstractmethod

from app.interfaces.generic_repository import GenericRepository
from app.models.user import User, UserRole


class UserRepository(GenericRepository[User], ABC):
    """Interface for User repository."""

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Find a user by email.

        Args:
            email (str): User email.

        Returns:
            User | None: User or none.
        """
        ...

    @abstractmethod
    async def count_recent(self, days: int) -> int:
        """Count number of users registered in the last N days.

        Args:
            days (int): Number of days to look back from today.

        Returns:
            int: Number of users registered in the last N days.
        """
        ...

    @abstractmethod
    async def find_all(
        self,
        *,
        role: UserRole | None = None,
        is_active: bool | None = None,
        is_deleted: bool | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[User], int]:
        """Find all users with optional filters, sorting, and pagination.

        Args:
            role (UserRole | None, optional): Filter by user role. Defaults to None.
            is_active (bool | None, optional): Filter by active status. Defaults to None.
            is_deleted (bool | None, optional): Filter by deleted status. Defaults to None.
            search (str | None, optional): Search query for email. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "created_at".
            sort_order (str, optional): Sort order, either "asc" or "desc". Defaults to "desc".
            page (int, optional): Page number. Defaults to 1.
            page_size (int, optional): Number of records per page. Defaults to 10.


        Returns:
            tuple[list[User], int]: List of users and total count.
        """
        ...
