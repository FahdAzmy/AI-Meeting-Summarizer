"""
tests/unit/test_db_adapters.py
-------------------------------
SPEC-10 compliance: confirm all legacy dual-mode adapter symbols have been
removed from src.models.meeting.

The original test_db_adapters.py tested parse_beanie_query, PostgresQueryResult,
and SQLMeeting — all part of the MongoDB/Beanie dual-mode architecture that was
intentionally deleted during the SPEC-10 database migration.
"""

import importlib
import inspect


def test_legacy_adapter_symbols_removed():
    """parse_beanie_query, PostgresQueryResult and SQLMeeting must not exist."""
    meeting_module = importlib.import_module("src.models.meeting")
    source = inspect.getsource(meeting_module)

    removed_symbols = ["parse_beanie_query", "PostgresQueryResult", "SQLMeeting"]
    for symbol in removed_symbols:
        assert symbol not in source, (
            f"Legacy symbol '{symbol}' was found in src.models.meeting — "
            "it must be removed as part of SPEC-10."
        )


def test_meeting_has_no_beanie_document():
    """Meeting must not inherit from Beanie Document."""
    meeting_module = importlib.import_module("src.models.meeting")
    source = inspect.getsource(meeting_module)
    assert "Document" not in source, (
        "Beanie 'Document' found in src.models.meeting — must be removed (SPEC-10)."
    )


def test_meeting_module_imports_cleanly():
    """src.models.meeting must be importable with no exceptions."""
    from src.models.meeting import Meeting, MeetingStatus  # noqa: F401
    assert Meeting.__tablename__ == "meetings"
    assert MeetingStatus.COMPLETED.value == "completed"
