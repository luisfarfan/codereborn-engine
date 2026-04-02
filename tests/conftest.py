"""
Pytest configuration and shared fixtures for CodeReborn Engine tests.

Strategy:
  - Use an in-memory SQLite database (aiosqlite) for unit/integration tests
    so tests can run without a real PostgreSQL instance.
  - Override the FastAPI DI to inject the test session.
  - Provide a pre-configured AsyncClient for HTTP-level tests.

Fixtures scope:
  - `engine`       → session  (one engine per test session)
  - `db_session`   → function (fresh tables + rollback per test)
  - `client`       → function (fresh app DI per test)
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.infrastructure.database import get_session
from app.main import app

# SQLite in-memory — avoids PostgreSQL-only types in tests.
# Tests that need JSONB behaviour should use a real DB (docker-compose up).
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    _engine = create_async_engine(TEST_DB_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Yields a fresh AsyncSession per test, rolling back after each."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """AsyncClient with overridden DB dependency for HTTP-level tests."""

    async def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
