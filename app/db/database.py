"""Database session management for asynchronous SQLModel operations."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select, text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole

async_engine = create_async_engine(
    url=settings.database_url,
    echo=False,
    pool_pre_ping=True,  # Verify connections before using them
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for the duration of a request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables() -> None:
    """Create database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def init_db() -> None:
    """Initialize the database."""
    # Optional: create tables for quick local dev (use Alembic in real flows)
    await create_tables()

    # Create superuser if not exists
    async with AsyncSessionLocal() as session:
        stmt = await session.exec(select(User).where(User.email == settings.superuser_email))
        user = stmt.first()
        if not user:
            new_user = User(
                email=settings.superuser_email,
                hashed_password=hash_password(settings.superuser_password),
                is_superuser=True,
                role=UserRole.ADMIN,
            )
            session.add(new_user)
            await session.commit()


async def check_db_health(session: AsyncSession) -> bool:
    """Attempts to execute a minimal query to verify database connection."""
    try:
        await session.exec(text("SELECT 1 "))  # type: ignore [call-overload]
        return True
    except Exception:
        return False
