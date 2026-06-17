# tests/unit/test_team_model.py
"""T10.04 — Team Model tests."""
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
