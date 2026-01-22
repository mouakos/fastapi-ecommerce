"""SQL generic repository implementation."""

from typing import Any
from uuid import UUID

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.interfaces.generic_repository import GenericRepository, T_model


class SqlGenericRepository(GenericRepository[T_model]):
    """SQL generic repository implementation."""

    def __init__(self, session: AsyncSession, model: type[T_model]) -> None:
        """Initialize the repository with a database session and model.

        Args:
            session (AsyncSession): The database session.
            model (type[T_model]): The model class.
        """
        self._session = session
        self._model = model

    async def find_by_id(self, id: UUID) -> T_model | None:
        """Find a single record by id.

        Args:
            id (UUID): Record id.

        Returns:
            T_model | None: Record or none.
        """
        return await self._session.get(self._model, id)

    async def list_all(self, **filters: Any) -> list[T_model]:  # noqa: ANN401
        """List records.

        Args:
            **filters: Filter conditions.

        Raises:
            ValueError: Invalid filter condition.

        Returns:
            list[T_model]: List of records.
        """
        stmt = select(self._model)
        for attr, value in filters.items():
            if not hasattr(self._model, attr):
                raise ValueError(f"Invalid filter condition: {attr}")
            stmt = stmt.where(getattr(self._model, attr) == value)
        result = await self._session.exec(stmt)
        return list(result.all())

    async def add(self, record: T_model) -> T_model:
        """Create a new record.

        Args:
            record (T_model): The record to be created.

        Returns:
            T_model: The created record.
        """
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def update(self, record: T_model) -> T_model:
        """Update an existing record.

        Args:
            record (T_model): The record to be updated incl. record id.

        Returns:
            T_model: The updated record.
        """
        return await self.add(record)

    async def delete(self, record: T_model) -> None:
        """Delete a record.

        Args:
            record (T_model): The record to be deleted.
        """
        await self._session.delete(record)
        await self._session.flush()

    async def count(self, **filters: Any) -> int:  # noqa: ANN401
        """Get total number of records.

        Args:
            **filters: Filter conditions.

        Returns:
            int: Total number of records.

        Raises:
            ValueError: Invalid filter condition.
        """
        stmt = select(func.count()).select_from(self._model)
        for attr, value in filters.items():
            if not hasattr(self._model, attr):
                raise ValueError(f"Invalid filter condition: {attr}")
            stmt = stmt.where(getattr(self._model, attr) == value)
        result = await self._session.exec(stmt)
        return result.first() or 0
