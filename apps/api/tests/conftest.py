import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from identity_api.config import get_settings
from identity_api.db import get_db
from identity_api.main import create_app
from identity_api.models import Base
from identity_api.redis_client import get_redis

# Use a dedicated DB so pytest drop_all does not wipe the migrate/dev schema.
# Redis DB index 1 keeps test keys off the default app DB (0).
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://identity:identity@localhost:5432/identity_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", "test-secret")
get_settings.cache_clear()


async def _ensure_test_database() -> None:
    """Create identity_test if missing (local Compose). Safe no-op if it exists."""
    admin_url = os.environ.get(
        "DATABASE_ADMIN_URL",
        "postgresql+asyncpg://identity:identity@localhost:5432/postgres",
    )
    eng = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with eng.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = 'identity_test'")
            )
            if not exists:
                await conn.execute(text("CREATE DATABASE identity_test"))
    finally:
        await eng.dispose()


@pytest.fixture
async def engine():
    await _ensure_test_database()
    settings = get_settings()
    eng = create_async_engine(settings.database_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def redis() -> AsyncGenerator[Redis, None]:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def client(engine, redis) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    async def override_get_redis() -> Redis:
        return redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
