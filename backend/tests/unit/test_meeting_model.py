# tests/unit/test_meeting_model.py
"""T10.06 — Meeting Model tests."""
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
    assert "Document" not in source        # no Beanie Document
    assert "BaseMeeting" not in source
    assert "PostgresQueryResult" not in source
