"""
Async database session factory for CodeReborn Engine.

Uses SQLAlchemy async engine with asyncpg driver.
All route handlers and services receive an AsyncSession via FastAPI DI.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,       # validate connections before use
    pool_size=10,
    max_overflow=20,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,   # keep objects usable after commit in async context
)


async def create_db_tables() -> None:
    """Create all tables defined in SQLModel metadata (used at startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession per request.
    Commits on success, rolls back on any exception.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
