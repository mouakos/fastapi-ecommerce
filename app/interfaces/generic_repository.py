"""Generic base repository interface."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import UUID

T_model = TypeVar("T_model")


class GenericRepository(Generic[T_model], ABC):  # noqa: UP046
    """Generic base repository."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> T_model | None:
        """Get a single record by id.

        Args:
            id (UUID): Record id.

        Returns:
            T_model | None: Record or none.
        """
        raise NotImplementedError()

    @abstractmethod
    async def list_all(self, **filters: Any) -> list[T_model]:  # noqa: ANN401
        """Gets a list of records.

        Args:
            **filters: Filter conditions.

        Raises:
            ValueError: Invalid filter condition.

        Returns:
            list[T_model]: List of records.
        """
        raise NotImplementedError()

    @abstractmethod
    async def add(self, record: T_model) -> T_model:
        """Creates a new record.

        Args:
            record (T_model): The record to be created.

        Returns:
            T_model: The created record.
        """
        raise NotImplementedError()

    @abstractmethod
    async def update(self, record: T_model) -> T_model:
        """Updates an existing record.

        Args:
            record (T_model): The record to be updated incl. record id.

        Returns:
            T_model: The updated record.
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        """Deletes a record by id.

        Args:
            id (UUID): Record id.
        """
        raise NotImplementedError()
