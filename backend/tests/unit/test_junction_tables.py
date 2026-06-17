# tests/unit/test_junction_tables.py
"""T10.07 — Junction Tables tests."""
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
