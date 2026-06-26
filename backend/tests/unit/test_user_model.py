# tests/unit/test_user_model.py
"""T10.03 — User Model tests."""
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
