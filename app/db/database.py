"""Database session management for asynchronous SQLModel operations."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models import *  # noqa: F403, F401

async_engine = create_async_engine(
    url=settings.database_url,
    echo=True,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for the duration of a request."""
    async with AsyncSession(async_engine) as s:
        yield s


# Optional: create tables for quick local dev (use Alembic in real flows)
async def init_db() -> None:
    """Create database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def check_db_health(session: AsyncSession) -> bool:
    """Attempts to execute a minimal query to verify database connection."""
    try:
        await session.exec(text("SELECT 1 "))  # type: ignore [call-overload]
        return True
    except Exception:
        return False
