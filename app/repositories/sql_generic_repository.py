"""SQLModel generic repository implementation."""

from typing import Any
from uuid import UUID

from sqlmodel import delete, select, update
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

    async def get_by_id(self, id: UUID) -> T_model | None:
        """Get a single record by id.

        Args:
            id (UUID): Record id.

        Returns:
            T_model | None: Record or none.
        """
        return await self._session.get(self._model, id)

    async def list_all(self, **filters: Any) -> list[T_model]:  # noqa: ANN401
        """Gets a list of records.

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
        """Creates a new record.

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
        """Updates an existing record.

        Args:
            record (T_model): The record to be updated incl. record id.

        Returns:
            T_model: The updated record.
        """
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def update_by_id(self, id: UUID, fields: dict[str, Any]) -> T_model | None:
        """Updates specific fields of a record by id.

        Args:
            id (UUID): Record id.
            fields (dict[str, Any]): Fields to update.

        Returns:
            T_model: The updated record
        """
        stmt = (
            update(self._model)
            .where(self._model.id == id)  # type: ignore[arg-type]
            .values(**fields)
            .returning(self._model)
        )
        result = await self._session.exec(stmt)
        return result.first()  # type: ignore[return-value]

    async def delete_by_id(self, id: UUID) -> bool:
        """Deletes a record by id.

        Args:
            id (UUID): Record id.
        """
        result = await self._session.exec(
            delete(self._model).where(self._model.id == id)  # type: ignore[arg-type]
        )
        if result.rowcount > 0:
            await self._session.flush()
            return True
        return False
