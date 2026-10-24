"""Pytest configuration and async fixtures for test suite."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from enterprise_api.core.database import get_db
from enterprise_api.core.security import hash_password
from enterprise_api.main import app
from enterprise_api.models import Base
from enterprise_api.models.enums import UserRole
from enterprise_api.models.user import User

# In-memory SQLite with StaticPool ensures all connections share the same memory DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Create all database schema before each test and tear down after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional test session."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an HTTPX async test client with dependency-overridden database."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Fixture ensuring a pre-seeded admin user exists in DB."""
    admin = User(
        email="testadmin@tasksphere.io",
        full_name="Test Administrator",
        hashed_password=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_member(db_session: AsyncSession) -> User:
    """Fixture ensuring a standard member user exists in DB."""
    member = User(
        email="testmember@tasksphere.io",
        full_name="Test Standard Member",
        hashed_password=hash_password("MemberPass123!"),
        role=UserRole.MEMBER,
        is_active=True,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    return member


@pytest.fixture
async def admin_token(client: AsyncClient, test_admin: User) -> str:
    """Obtain a Bearer JWT token for test_admin."""
    resp = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "testadmin@tasksphere.io", "password": "AdminPass123!"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
async def member_token(client: AsyncClient, test_member: User) -> str:
    """Obtain a Bearer JWT token for test_member."""
    resp = await client.post(
        "/api/v1/auth/login/json",
        json={"username": "testmember@tasksphere.io", "password": "MemberPass123!"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]
