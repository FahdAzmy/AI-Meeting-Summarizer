# SPEC-10: Database Migration & Data Models

| Field            | Details                                                    |
|------------------|------------------------------------------------------------|
| **Scope**        | PostgreSQL-only migration + All new SQLAlchemy models      |
| **Files**        | `src/helpers/db.py`, `src/helpers/config.py`, `config/settings.py`, `src/models/*`, `alembic/` |
| **Traceability** | Phases 1 & 2 — Database Foundation + Entity Models         |
| **Framework**    | SQLAlchemy 2.x (async) + Alembic + asyncpg                |
| **Version**      | 1.0                                                        |
| **Date**         | June 17, 2026                                              |

---

## 10.1 Objective

Remove the dual-database abstraction (MongoDB/Beanie + PostgreSQL/SQLAlchemy) and establish a **PostgreSQL-only** data layer with:
- Clean async SQLAlchemy models for all entities
- Alembic migration tooling
- Proper foreign key relationships and tenant isolation via `company_id`

> **Breaking Change:** All MongoDB code (`motor`, `beanie`, `AsyncIOMotorClient`, `init_beanie`, `get_client()`) will be fully removed. The `DATABASE_TYPE` conditional branching is eliminated.

---

## 10.2 Test Plan (TDD — Tests First)

All tests use `pytest` + `pytest-asyncio` with a test PostgreSQL database.

### T10.01 — Database Connection

```python
# tests/unit/test_db_connection.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_init_db_creates_engine(test_db):
    """init_db() should create a valid async engine and session factory."""
    from src.helpers.db import postgres_engine, SessionLocal
    assert postgres_engine is not None
    assert SessionLocal is not None

@pytest.mark.asyncio
async def test_get_db_yields_session(test_db):
    """get_db() dependency should yield an AsyncSession."""
    from src.helpers.db import get_db
    async for session in get_db():
        assert isinstance(session, AsyncSession)

@pytest.mark.asyncio
async def test_no_mongodb_imports():
    """Ensure no MongoDB dependencies are imported anywhere in db.py."""
    import inspect
    from src.helpers import db
    source = inspect.getsource(db)
    assert "motor" not in source
    assert "beanie" not in source
    assert "AsyncIOMotorClient" not in source
```

### T10.02 — Company Model

```python
# tests/unit/test_company_model.py
import pytest
from uuid import UUID

@pytest.mark.asyncio
async def test_create_company(db_session):
    """Should create a company with UUID primary key."""
    from src.models.company import Company
    company = Company(name="Acme Corp", subscription_plan="pro")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    assert isinstance(company.id, UUID)
    assert company.name == "Acme Corp"
    assert company.subscription_plan == "pro"

@pytest.mark.asyncio
async def test_company_name_unique(db_session):
    """Should reject duplicate company names."""
    from src.models.company import Company
    from sqlalchemy.exc import IntegrityError
    db_session.add(Company(name="Acme Corp"))
    await db_session.commit()
    db_session.add(Company(name="Acme Corp"))
    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_company_default_plan(db_session):
    """Default subscription_plan should be 'free'."""
    from src.models.company import Company
    company = Company(name="NewCo")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    assert company.subscription_plan == "free"
```

### T10.03 — User Model

```python
# tests/unit/test_user_model.py
import pytest
from uuid import UUID

@pytest.mark.asyncio
async def test_create_user(db_session, sample_company):
    """Should create a user linked to a company."""
    from src.models.user import User, UserRole
    user = User(
        name="Ahmed Ali",
        email="ahmed@acme.com",
        password="hashed_pw",
        role=UserRole.HR,
        company_id=sample_company.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert isinstance(user.id, UUID)
    assert user.role == UserRole.HR
    assert user.company_id == sample_company.id

@pytest.mark.asyncio
async def test_user_email_unique(db_session, sample_company):
    """Should reject duplicate email addresses."""
    from src.models.user import User, UserRole
    from sqlalchemy.exc import IntegrityError
    db_session.add(User(name="A", email="dup@test.com", password="pw", role=UserRole.HR, company_id=sample_company.id))
    await db_session.commit()
    db_session.add(User(name="B", email="dup@test.com", password="pw", role=UserRole.HR, company_id=sample_company.id))
    with pytest.raises(IntegrityError):
        await db_session.commit()

@pytest.mark.asyncio
async def test_user_role_enum(db_session, sample_company):
    """Should only accept valid UserRole values (hr, team_leader)."""
    from src.models.user import User, UserRole
    user = User(name="X", email="x@t.com", password="pw", role=UserRole.TEAM_LEADER, company_id=sample_company.id)
    db_session.add(user)
    await db_session.commit()
    assert user.role == UserRole.TEAM_LEADER
```

### T10.04 — Team Model

```python
# tests/unit/test_team_model.py
import pytest

@pytest.mark.asyncio
async def test_create_team(db_session, sample_company):
    """Should create a team linked to a company."""
    from src.models.team import Team
    team = Team(name="Backend Team", company_id=sample_company.id)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    assert team.name == "Backend Team"
    assert team.leader_id is None  # leader is optional

@pytest.mark.asyncio
async def test_assign_team_leader(db_session, sample_company, sample_user):
    """Should allow assigning a leader to a team."""
    from src.models.team import Team
    team = Team(name="Dev Team", company_id=sample_company.id, leader_id=sample_user.id)
    db_session.add(team)
    await db_session.commit()
    assert team.leader_id == sample_user.id
```

### T10.05 — Member Model

```python
# tests/unit/test_member_model.py
import pytest

@pytest.mark.asyncio
async def test_create_member(db_session, sample_company, sample_team):
    """Should create a member linked to a team and company."""
    from src.models.member import Member
    member = Member(
        name="Fahd Azmy",
        email="fahd@acme.com",
        team_id=sample_team.id,
        company_id=sample_company.id,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)
    assert member.name == "Fahd Azmy"
    assert member.team_id == sample_team.id

@pytest.mark.asyncio
async def test_member_cascade_on_team_delete(db_session, sample_company, sample_team):
    """Members should be deleted when their team is deleted."""
    from src.models.member import Member
    from sqlalchemy import select
    member = Member(name="Test", email="t@t.com", team_id=sample_team.id, company_id=sample_company.id)
    db_session.add(member)
    await db_session.commit()
    await db_session.delete(sample_team)
    await db_session.commit()
    result = await db_session.execute(select(Member).where(Member.id == member.id))
    assert result.scalar_one_or_none() is None
```

### T10.06 — Meeting Model (Simplified)

```python
# tests/unit/test_meeting_model.py
import pytest
from src.models.meeting import MeetingStatus

@pytest.mark.asyncio
async def test_create_meeting(db_session, sample_company, sample_user):
    """Should create a meeting with company_id and created_by."""
    from src.models.meeting import Meeting
    meeting = Meeting(
        meeting_link="https://meet.google.com/abc",
        platform="Google Meet",
        company_id=sample_company.id,
        created_by=sample_user.id,
    )
    db_session.add(meeting)
    await db_session.commit()
    await db_session.refresh(meeting)
    assert meeting.status == MeetingStatus.PROCESSING
    assert meeting.company_id == sample_company.id

@pytest.mark.asyncio
async def test_meeting_no_mongodb_code():
    """Meeting model should have no MongoDB/Beanie references."""
    import inspect
    from src.models import meeting
    source = inspect.getsource(meeting)
    assert "Document" not in source  # no Beanie Document
    assert "BaseMeeting" not in source
    assert "PostgresQueryResult" not in source
```

### T10.07 — Junction Tables

```python
# tests/unit/test_junction_tables.py
import pytest

@pytest.mark.asyncio
async def test_meeting_team_association(db_session, sample_meeting, sample_team):
    """Should link a meeting to a team via MeetingTeam."""
    from src.models.meeting_team import MeetingTeam
    mt = MeetingTeam(meeting_id=sample_meeting.id, team_id=sample_team.id)
    db_session.add(mt)
    await db_session.commit()

@pytest.mark.asyncio
async def test_meeting_participant_association(db_session, sample_meeting, sample_member):
    """Should link a meeting to a member via MeetingParticipant."""
    from src.models.meeting_participant import MeetingParticipant
    mp = MeetingParticipant(meeting_id=sample_meeting.id, member_id=sample_member.id)
    db_session.add(mp)
    await db_session.commit()
```

### T10.08 — Alembic Migrations

```python
# tests/unit/test_alembic.py
import subprocess

def test_alembic_heads():
    """Should have exactly one migration head (no branching)."""
    result = subprocess.run(
        ["alembic", "heads"], capture_output=True, text=True, cwd="."
    )
    heads = [l for l in result.stdout.strip().split("\n") if l.strip()]
    assert len(heads) == 1

def test_alembic_upgrade_succeeds(test_db_url):
    """alembic upgrade head should apply all migrations without error."""
    result = subprocess.run(
        ["alembic", "upgrade", "head"], capture_output=True, text=True, cwd="."
    )
    assert result.returncode == 0
```

---

## 10.3 Database Connection (Simplified)

```python
# src/helpers/db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.helpers.config import settings
import logging

logger = logging.getLogger("app")

postgres_engine = None
SessionLocal = None

async def init_db():
    """Initialize PostgreSQL connection and create tables."""
    global postgres_engine, SessionLocal
    logger.info("Initializing PostgreSQL connection …")

    db_url = settings.get_database_url()
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    postgres_engine = create_async_engine(db_url, echo=False, future=True)
    SessionLocal = async_sessionmaker(
        bind=postgres_engine, class_=AsyncSession, expire_on_commit=False
    )

    from src.models.base import Base
    async with postgres_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("PostgreSQL connection established and tables verified")

async def get_db():
    """Dependency to get a PostgreSQL database session."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized.")
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## 10.4 Entity Models

### 10.4.1 Shared Base

```python
# src/models/base.py
from sqlalchemy.orm import declarative_base

Base = declarative_base()
```

### 10.4.2 Company

```python
# src/models/company.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    subscription_plan = Column(String(50), nullable=False, default="free")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
```

### 10.4.3 User

```python
# src/models/user.py
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base

class UserRole(str, PyEnum):
    HR = "hr"
    TEAM_LEADER = "team_leader"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### 10.4.4 Team

```python
# src/models/team.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    leader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### 10.4.5 Member

```python
# src/models/member.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base

class Member(Base):
    __tablename__ = "members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### 10.4.6 Meeting (Rewritten — PostgreSQL Only)

```python
# src/models/meeting.py
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base

class MeetingStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    JOINING = "joining"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    SUMMARISING = "summarising"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=True)
    meeting_link = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    platform = Column(String(50), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(SQLEnum(MeetingStatus), nullable=False, default=MeetingStatus.PROCESSING)
    error_message = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    action_items = Column(JSON, nullable=True, default=list)
    decisions = Column(JSON, nullable=True, default=list)
    follow_up = Column(JSON, nullable=True, default=list)
    speaker_stats = Column(JSON, nullable=True)

    # Tenant isolation
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
```

### 10.4.7 Junction Tables

```python
# src/models/meeting_team.py
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base

class MeetingTeam(Base):
    __tablename__ = "meeting_teams"
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
```

```python
# src/models/meeting_participant.py
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base

class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), primary_key=True)
```

---

## 10.5 Models `__init__.py`

```python
# src/models/__init__.py
from src.models.base import Base
from src.models.company import Company
from src.models.user import User, UserRole
from src.models.team import Team
from src.models.member import Member
from src.models.meeting import Meeting, MeetingStatus
from src.models.meeting_team import MeetingTeam
from src.models.meeting_participant import MeetingParticipant

__all__ = [
    "Base", "Company", "User", "UserRole", "Team", "Member",
    "Meeting", "MeetingStatus", "MeetingTeam", "MeetingParticipant",
]
```

---

## 10.6 ER Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  companies   │       │    users     │       │    teams     │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │◄──┐   │ id (PK)      │   ┌──►│ id (PK)      │
│ name (UQ)    │   │   │ name         │   │   │ name         │
│ subscription │   ├───│ company_id   │   │   │ leader_id ──►│ users.id
│ created_at   │   │   │ email (UQ)   │   ├───│ company_id   │
│ updated_at   │   │   │ password     │   │   │ created_at   │
└──────────────┘   │   │ role         │   │   └──────┬───────┘
                   │   │ is_active    │   │          │
                   │   │ created_at   │   │          │
                   │   └──────────────┘   │          │
                   │                      │          │
                   │   ┌──────────────┐   │   ┌──────▼───────┐
                   │   │   meetings   │   │   │   members    │
                   │   ├──────────────┤   │   ├──────────────┤
                   │   │ id (PK)      │   │   │ id (PK)      │
                   ├───│ company_id   │   │   │ name         │
                   │   │ created_by ──►   │   │ email        │
                   │   │ title        │   └───│ team_id      │
                   │   │ meeting_link │       │ company_id ──►
                   │   │ session_id   │       │ created_at   │
                   │   │ platform     │       └──────────────┘
                   │   │ scheduled_time│
                   │   │ status       │
                   │   │ ...          │
                   │   └──────┬───────┘
                   │          │
          ┌────────┴──────────┼────────────────┐
          │                   │                │
   ┌──────▼───────┐   ┌──────▼───────┐
   │ meeting_teams│   │meeting_parts │
   ├──────────────┤   ├──────────────┤
   │ meeting_id   │   │ meeting_id   │
   │ team_id      │   │ member_id    │
   └──────────────┘   └──────────────┘
```

---

## 10.7 Configuration Changes

### Settings to Remove
- `DATABASE_TYPE`, `MONGO_URI`, `MONGO_DB`, `MONGO_TEST_DB`

### Dependencies to Remove
- `motor`, `beanie`

### Dependencies to Add
- `alembic>=1.13.0`

---

## 10.8 Alembic Setup

```ini
# alembic.ini (key settings)
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5433/ai_summarizer
```

```python
# alembic/env.py — async migration support
from src.models.base import Base
target_metadata = Base.metadata
```

---

## 10.9 Acceptance Criteria

| #  | Criteria                                                                      | Verified |
|----|-------------------------------------------------------------------------------|----------|
| 1  | All MongoDB imports and code removed from `db.py`, `config.py`, `settings.py` | ☐        |
| 2  | `motor` and `beanie` removed from `requirements.txt`                         | ☐        |
| 3  | `alembic upgrade head` creates all 7 tables with correct columns             | ☐        |
| 4  | Company.name has UNIQUE constraint                                           | ☐        |
| 5  | User.email has UNIQUE constraint                                             | ☐        |
| 6  | All FK relationships enforced (company→user, company→team, etc.)             | ☐        |
| 7  | Meeting model is a simple SQLAlchemy model (no Beanie/dual-mode code)        | ☐        |
| 8  | CASCADE delete: deleting a team deletes its members                          | ☐        |
| 9  | CASCADE delete: deleting a meeting deletes its meeting_teams/participants    | ☐        |
| 10 | All T10.01–T10.08 tests pass                                                | ☐        |
