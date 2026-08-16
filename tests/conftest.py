import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app import database
from app.config import settings
from app.main import app


@pytest.fixture(autouse=True)
async def reset_db_engine():
    """Use NullPool per test to prevent asyncpg connections leaking across event loops."""
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    original_engine = database.engine
    original_factory = database.async_session_factory
    database.engine = engine
    database.async_session_factory = factory

    yield

    database.engine = original_engine
    database.async_session_factory = original_factory
    await engine.dispose()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
