"""Generic base repository interface."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar
from uuid import UUID

from app.models.common import ModelBase

T_model = TypeVar("T_model", bound=ModelBase)


class GenericRepository[T_model](ABC):
    """Generic base repository."""

    @abstractmethod
    async def find_by_id(self, id: UUID) -> T_model | None:
        """Find a single record by id.

        Args:
            id (UUID): Record id.

        Returns:
            T_model | None: Record or none.
        """
        ...

    @abstractmethod
    async def list_all(self, **filters: Any) -> list[T_model]:  # noqa: ANN401
        """List records.

        Args:
            **filters: Filter conditions.

        Raises:
            ValueError: Invalid filter condition.

        Returns:
            list[T_model]: List of records.
        """
        ...

    @abstractmethod
    async def add(self, record: T_model) -> T_model:
        """Create a new record.

        Args:
            record (T_model): The record to be created.

        Returns:
            T_model: The created record.
        """
        ...

    @abstractmethod
    async def update(self, record: T_model) -> T_model:
        """Update an existing record.

        Args:
            record (T_model): The record to be updated incl. record id.

        Returns:
            T_model: The updated record.
        """
        ...

    @abstractmethod
    async def delete(self, record: T_model) -> None:
        """Delete a record by id.

        Args:
            record (T_model): The record to be deleted.

        """
        ...

    @abstractmethod
    async def count(self, **filters: Any) -> int:  # noqa: ANN401
        """Count total number of records.

        Args:
            **filters: Filter conditions.

        Returns:
            int: Total number of records.

        Raises:
            ValueError: If invalid filters are provided.
        """
        ...
