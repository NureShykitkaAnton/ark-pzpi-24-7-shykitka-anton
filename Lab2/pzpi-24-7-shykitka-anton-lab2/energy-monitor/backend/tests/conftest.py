"""Конфігурація тестового середовища pytest з підключенням до СУБД PostgreSQL 18."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_db
from app.core.models import Base
from app.main import app

test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(loop_scope="function", autouse=True)
async def setup_database() -> AsyncGenerator[None]:
    """Ініціалізує схему таблиць перед кожним тестом."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(loop_scope="function")
async def async_client() -> AsyncGenerator[AsyncClient]:
    """Повертає асинхронний HTTP-клієнт для тестування ендпоінтів FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="https://api.energymon.localhost"
    ) as client:
        yield client
