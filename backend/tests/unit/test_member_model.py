# tests/unit/test_member_model.py
"""T10.05 — Member Model tests."""
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
