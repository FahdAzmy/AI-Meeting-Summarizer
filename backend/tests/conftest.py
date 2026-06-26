"""
tests/conftest.py
-----------------
Shared pytest fixtures for the SPEC-10 database migration test suite.
"""

import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
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


@pytest_asyncio.fixture()
async def async_client(test_db):
    """HTTPX async client bound to the FastAPI app without running lifespan."""
    from src.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture()
async def registered_user(async_client):
    payload = {
        "name": "Registered HR",
        "email": "registered@testco.com",
        "password": "Pass123!",
        "company_name": "Registered Co",
    }
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    return payload


@pytest_asyncio.fixture()
async def auth_tokens(async_client, registered_user):
    response = await async_client.post(
        "/api/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    return response.json()


@pytest_asyncio.fixture()
async def hr_auth_headers(sample_user):
    from src.helpers.security import generate_access_token

    token = generate_access_token(sample_user.id, sample_user.role, sample_user.company_id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture()
async def tl_user(db_session, sample_company):
    from src.helpers.security import hash_password
    from src.models.user import User, UserRole

    user = User(
        name="Team Lead",
        email="lead@testco.com",
        password=hash_password("Pass123!"),
        role=UserRole.TEAM_LEADER,
        company_id=sample_company.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def tl_auth_headers(tl_user):
    from src.helpers.security import generate_access_token

    token = generate_access_token(tl_user.id, tl_user.role, tl_user.company_id)
    return {"Authorization": f"Bearer {token}"}


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
async def sample_teams(db_session, sample_company):
    from src.models.team import Team

    teams = [
        Team(name="Backend", company_id=sample_company.id),
        Team(name="Frontend", company_id=sample_company.id),
    ]
    db_session.add_all(teams)
    await db_session.commit()
    for team in teams:
        await db_session.refresh(team)
    return teams


@pytest_asyncio.fixture()
async def sample_tl_user(tl_user):
    return tl_user


@pytest_asyncio.fixture()
async def tl_team(db_session, sample_company, tl_user):
    from src.models.team import Team

    team = Team(
        name="Lead Team",
        company_id=sample_company.id,
        leader_id=tl_user.id,
    )
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture()
async def other_team(db_session, sample_company):
    from src.models.team import Team

    team = Team(name="Other Team", company_id=sample_company.id)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture()
async def company_b(db_session):
    from src.models.company import Company

    company = Company(name="Company B", subscription_plan="pro")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture()
async def company_a(sample_company):
    return sample_company


@pytest_asyncio.fixture()
async def hr_b_user(db_session, company_b):
    from src.models.user import User, UserRole

    user = User(
        name="Company B HR",
        email="hrb@testco.com",
        password="hashed_pw",
        role=UserRole.HR,
        company_id=company_b.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def hr_b_headers(hr_b_user):
    from src.helpers.security import generate_access_token

    token = generate_access_token(hr_b_user.id, hr_b_user.role, hr_b_user.company_id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture()
async def company_b_team(db_session, company_b):
    from src.models.team import Team

    team = Team(name="Company B Team", company_id=company_b.id)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture()
async def sample_team_with_members(db_session, sample_company):
    from src.models.member import Member
    from src.models.team import Team

    team = Team(name="Team With Members", company_id=sample_company.id)
    db_session.add(team)
    await db_session.flush()
    db_session.add_all(
        [
            Member(name="A One", email="a1@testco.com", team_id=team.id, company_id=sample_company.id),
            Member(name="A Two", email="a2@testco.com", team_id=team.id, company_id=sample_company.id),
            Member(name="A Three", email="a3@testco.com", team_id=team.id, company_id=sample_company.id),
        ]
    )
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture()
async def sample_members(db_session, sample_company, sample_team):
    from src.models.member import Member

    members = [
        Member(name="Member One", email="one@testco.com", team_id=sample_team.id, company_id=sample_company.id),
        Member(name="Member Two", email="two@testco.com", team_id=sample_team.id, company_id=sample_company.id),
    ]
    db_session.add_all(members)
    await db_session.commit()
    for member in members:
        await db_session.refresh(member)
    return members


@pytest_asyncio.fixture()
async def member_in_team(sample_member):
    return sample_member


@pytest_asyncio.fixture()
async def meeting_a(sample_meeting):
    return sample_meeting


@pytest_asyncio.fixture()
async def seeded_data(db_session, sample_company, sample_user, tl_user):
    from src.models.meeting import Meeting, MeetingStatus
    from src.models.meeting_team import MeetingTeam
    from src.models.member import Member
    from src.models.team import Team

    led_team = Team(name="Led Team", company_id=sample_company.id, leader_id=tl_user.id)
    other_team = Team(name="Ops Team", company_id=sample_company.id)
    db_session.add_all([led_team, other_team])
    await db_session.flush()

    members = [
        Member(name="One", email="one@seed.test", team_id=led_team.id, company_id=sample_company.id),
        Member(name="Two", email="two@seed.test", team_id=led_team.id, company_id=sample_company.id),
        Member(name="Three", email="three@seed.test", team_id=other_team.id, company_id=sample_company.id),
    ]
    db_session.add_all(members)

    meetings = [
        Meeting(
            title="Planning",
            meeting_link="https://meet.google.com/seed-one",
            duration_minutes=60,
            summary="Done",
            action_items=[{"task": "A"}, {"task": "B"}],
            status=MeetingStatus.COMPLETED,
            company_id=sample_company.id,
            created_by=sample_user.id,
        ),
        Meeting(
            title="Review",
            meeting_link="https://meet.google.com/seed-two",
            duration_minutes=30,
            summary="Done",
            action_items=[{"task": "C"}],
            status=MeetingStatus.COMPLETED,
            company_id=sample_company.id,
            created_by=sample_user.id,
        ),
    ]
    db_session.add_all(meetings)
    await db_session.flush()
    db_session.add_all(
        [
            MeetingTeam(meeting_id=meetings[0].id, team_id=led_team.id),
            MeetingTeam(meeting_id=meetings[1].id, team_id=other_team.id),
        ]
    )
    await db_session.commit()
    return {
        "teams_count": 2,
        "members_count": 3,
        "meetings_count": 2,
        "led_team": led_team,
        "other_team": other_team,
    }


@pytest_asyncio.fixture()
async def other_team_data(db_session, sample_company):
    from src.models.member import Member
    from src.models.team import Team

    team = Team(name="Unled Data Team", company_id=sample_company.id)
    db_session.add(team)
    await db_session.flush()
    db_session.add(
        Member(
            name="Other Member",
            email="other-data@testco.com",
            team_id=team.id,
            company_id=sample_company.id,
        )
    )
    await db_session.commit()
    return {"total_company_members": 1}


@pytest_asyncio.fixture()
async def empty_company_hr_headers(db_session):
    from src.helpers.security import generate_access_token
    from src.models.company import Company
    from src.models.user import User, UserRole

    company = Company(name="Empty Company", subscription_plan="free")
    db_session.add(company)
    await db_session.flush()
    user = User(
        name="Empty HR",
        email="empty@testco.com",
        password="hashed_pw",
        role=UserRole.HR,
        company_id=company.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    token = generate_access_token(user.id, user.role, user.company_id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture()
async def hr_a_headers(hr_auth_headers):
    return hr_auth_headers


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
