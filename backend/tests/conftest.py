"""
tests/conftest.py
-----------------
Shared pytest fixtures for the SPEC-10 database migration test suite.
"""

import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import pool
from src.models.base import Base
from src.helpers.config import settings

# ── Database URL selection ───────────────────────────────────────────────────
TEST_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or (
    f"postgresql+asyncpg://"
    f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)
if TEST_URL.startswith("postgresql://"):
    TEST_URL = TEST_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


@pytest_asyncio.fixture()
async def test_engine():
    """Create a function-scoped async engine matching the test's event loop."""
    engine = create_async_engine(TEST_URL, echo=False, future=True, poolclass=pool.NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def test_db(test_engine):
    """Create all tables for each test, drop them on teardown."""
    import src.models  # noqa: F401

    # Populate database tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Configure session factory
    session_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Expose engine/session in db.py globals so db functions work
    from src.helpers import db as db_module
    db_module.postgres_engine = test_engine
    db_module.SessionLocal = session_factory

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session(test_db):
    """Provide a single AsyncSession that is rolled back after each test."""
    from src.helpers.db import SessionLocal
    async with SessionLocal() as session:
        yield session
        await session.rollback()


# ── Data fixtures ─────────────────────────────────────────────────────────────
@pytest_asyncio.fixture()
async def sample_company(db_session):
    from src.models.company import Company
    company = Company(name="Test Company", subscription_plan="pro")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture()
async def sample_user(db_session, sample_company):
    from src.models.user import User, UserRole
    user = User(
        name="Test User",
        email="test@testco.com",
        password="hashed_pw",
        role=UserRole.HR,
        company_id=sample_company.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def sample_team(db_session, sample_company):
    from src.models.team import Team
    team = Team(name="Test Team", company_id=sample_company.id)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture()
async def sample_member(db_session, sample_company, sample_team):
    from src.models.member import Member
    member = Member(
        name="Test Member",
        email="member@testco.com",
        team_id=sample_team.id,
        company_id=sample_company.id,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    return member


@pytest_asyncio.fixture()
async def sample_meeting(db_session, sample_company, sample_user):
    from src.models.meeting import Meeting
    meeting = Meeting(
        meeting_link="https://meet.google.com/test",
        platform="Google Meet",
        company_id=sample_company.id,
        created_by=sample_user.id,
    )
    db_session.add(meeting)
    await db_session.commit()
    await db_session.refresh(meeting)
    return meeting


# ── Utility fixtures ──────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def test_db_url():
    """Raw database URL string for subprocess-based tests (T10.08)."""
    return TEST_URL
