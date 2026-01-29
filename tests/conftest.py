import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test SECRET_KEY before importing app modules
os.environ["SECRET_KEY"] = "test-secret-key-must-be-at-least-32-characters-long"


class AsyncIterator:
    """Async iterator for mocking redis.scan_iter."""

    def __init__(self, items):
        self.items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.items)
        except StopIteration as err:
            raise StopAsyncIteration from err


# Create a fake redis client for tests
_fake_redis_client = MagicMock()
_fake_redis_client.setex = AsyncMock(return_value=True)
_fake_redis_client.get = AsyncMock(return_value=None)
_fake_redis_client.exists = AsyncMock(return_value=True)
_fake_redis_client.delete = AsyncMock(return_value=1)
_fake_redis_client.scan_iter = MagicMock(return_value=AsyncIterator([]))
_fake_redis_client.close = AsyncMock()


async def _mock_get_redis():
    return _fake_redis_client


# Patch Redis at the module level before any imports
_redis_patcher = patch("app.core.redis.get_redis", _mock_get_redis)
_redis_patcher.start()

from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.user_service import UserService  # noqa: E402

# Also patch where it's imported in security.py
patch("app.core.security.get_redis", _mock_get_redis).start()

# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for authenticated tests."""
    from app.schemas.user import UserCreate

    service = UserService(db_session)
    user_data = UserCreate(
        email="testuser@example.com",
        password="TestPassword123!",  # Meets new password policy
        full_name="Test User",
    )
    user = await service.create(user_data)
    await db_session.commit()
    return user


@pytest.fixture
async def auth_headers(test_user: User) -> dict:
    """Get auth headers for authenticated requests."""
    token, _ = create_access_token(subject=test_user.id)  # Unpack tuple
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def superuser(db_session: AsyncSession) -> User:
    """Create a superuser for admin tests."""
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("AdminPassword123!"),  # Meets new password policy
        full_name="Admin User",
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    await db_session.commit()
    return user


@pytest.fixture
async def superuser_headers(superuser: User) -> dict:
    """Get auth headers for superuser requests."""
    token, _ = create_access_token(subject=superuser.id)  # Unpack tuple
    return {"Authorization": f"Bearer {token}"}
