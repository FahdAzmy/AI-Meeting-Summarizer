"""
tests/unit/test_pdf_generator.py
---------------------------------
TDD test suite for the PDF generation helper.

Tests are written FIRST (before implementation) following Constitution Principle I.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any
from unittest.mock import MagicMock
from datetime import datetime, timezone

import pytest


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def _make_mock_meeting(**overrides: Any) -> MagicMock:
    meeting = MagicMock()
    meeting.title = overrides.get("title", "Sprint Standup")
    meeting.platform = overrides.get("platform", "Google Meet")
    meeting.created_at = overrides.get("created_at", datetime(2026, 4, 26, 14, 0, tzinfo=timezone.utc))
    meeting.duration_minutes = overrides.get("duration_minutes", 45)
    meeting.summary = overrides.get("summary", "Team discussed sprint goals and agreed on timeline.")
    meeting.decisions = overrides.get("decisions", ["Approved Q3 plan", "Budget allocated"])
    meeting.action_items = overrides.get(
        "action_items",
        [{"assignee": "Alice", "task": "Write spec", "deadline": "Friday"}],
    )
    meeting.follow_up = overrides.get("follow_up", ["Schedule retro"])
    meeting.speaker_stats = overrides.get("speaker_stats", {
        "speakers": [
            {"speaker": "Alice", "total_speaking_time_sec": 120},
            {"speaker": "Bob", "total_speaking_time_sec": 80},
        ]
    })
    meeting.transcript = overrides.get("transcript", "Alice: Let's begin. Bob: Agreed, let's go.")
    return meeting


# ---------------------------------------------------------------------------
# T016 — PDF generator: generate_meeting_pdf
# ---------------------------------------------------------------------------

class TestGenerateMeetingPdf:
    """T016: generate_meeting_pdf must return a valid PDF BytesIO buffer."""

    def test_returns_bytes_io(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting()
        result = generate_meeting_pdf(meeting)
        assert isinstance(result, BytesIO)

    def test_pdf_starts_with_pdf_header(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting()
        buf = generate_meeting_pdf(meeting)
        content = buf.read()
        assert content[:5] == b"%PDF-"

    def test_pdf_is_non_empty(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting()
        buf = generate_meeting_pdf(meeting)
        assert buf.getbuffer().nbytes > 100

    def test_title_fallback_when_none(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting(title=None, platform="Zoom")
        buf = generate_meeting_pdf(meeting)
        assert buf.getbuffer().nbytes > 100

    def test_handles_empty_decisions(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting(decisions=[])
        buf = generate_meeting_pdf(meeting)
        assert buf.getbuffer().nbytes > 100

    def test_handles_empty_action_items(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting(action_items=[])
        buf = generate_meeting_pdf(meeting)
        assert buf.getbuffer().nbytes > 100

    def test_handles_no_transcript(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting(transcript=None)
        buf = generate_meeting_pdf(meeting)
        assert buf.getbuffer().nbytes > 100

    def test_handles_no_speaker_stats(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting(speaker_stats=None)
        buf = generate_meeting_pdf(meeting)
        assert buf.getbuffer().nbytes > 100

    def test_handles_empty_follow_up(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting(follow_up=[])
        buf = generate_meeting_pdf(meeting)
        assert buf.getbuffer().nbytes > 100

    def test_handles_all_empty_sections(self) -> None:
        from src.helpers.pdf_generator import generate_meeting_pdf
        meeting = _make_mock_meeting(
            summary=None, decisions=[], action_items=[],
            follow_up=[], transcript=None, speaker_stats=None
        )
        buf = generate_meeting_pdf(meeting)
        assert buf.getbuffer().nbytes > 100
