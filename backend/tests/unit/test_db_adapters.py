import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.models.meeting import Meeting, parse_beanie_query, PostgresQueryResult, SQLMeeting, MeetingStatus

def test_parse_beanie_query():
    # Test dictionary
    res1 = parse_beanie_query([{"field": "val"}])
    assert res1 == {"field": "val"}

    # Test metaclass equality expression (simulated)
    class DummyExpr:
        def __init__(self, d):
            self.d = d
        def __iter__(self):
            return iter(self.d.items())
        def keys(self):
            return self.d.keys()
        def __getitem__(self, key):
            return self.d[key]

    res2 = parse_beanie_query([DummyExpr({"status": "completed"})])
    assert res2 == {"status": "completed"}

def test_metaclass_query_expression():
    # Accessing fields on Meeting class should return comparison dicts
    expr1 = (Meeting.session_id == "test-session")
    assert expr1 == {"session_id": "test-session"}

    expr2 = (Meeting.status == MeetingStatus.COMPLETED)
    assert expr2 == {"status": MeetingStatus.COMPLETED}

@pytest.mark.asyncio
async def test_postgres_query_result_to_list():
    # Mock SessionLocal and its connection
    mock_session = AsyncMock()
    mock_execute_result = MagicMock()
    
    # Mock SQLMeeting instances returned from DB
    sql_meeting_1 = SQLMeeting(
        id="meeting-1",
        title="Sync",
        created_at=None,
        status="completed",
        action_items=[],
        decisions=[],
        follow_up=[]
    )
    mock_execute_result.scalars().all.return_value = [sql_meeting_1]
    mock_session.execute.return_value = mock_execute_result

    # Mock DB SessionLocal context manager
    with patch("src.helpers.db.SessionLocal") as mock_session_local:
        # Configure mock context manager
        context_mock = AsyncMock()
        context_mock.__aenter__.return_value = mock_session
        mock_session_local.return_value = context_mock
        
        query_result = PostgresQueryResult(Meeting, {"status": "completed"})
        meetings = await query_result.to_list()
        
        assert len(meetings) == 1
        assert meetings[0].id == "meeting-1"
        assert meetings[0].status == MeetingStatus.COMPLETED
