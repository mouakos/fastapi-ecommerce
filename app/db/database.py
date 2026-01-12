"""Database session management for asynchronous SQLModel operations."""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

async_engine = create_async_engine(
    url=settings.database_url,
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Optional: create tables for quick local dev (use Alembic in real flows)
async def create_tables() -> None:
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
