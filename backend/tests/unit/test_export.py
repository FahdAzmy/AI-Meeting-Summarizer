"""
tests/unit/test_export.py
--------------------------
TDD test suite for the export API endpoints.

Tests are written FIRST (before implementation) following Constitution Principle I.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_mock_meeting(**overrides: Any) -> MagicMock:
    from datetime import datetime, timezone
    meeting = MagicMock()
    meeting.id = overrides.get("id", "507f1f77bcf86cd799439011")
    meeting.title = overrides.get("title", "Sprint Standup")
    meeting.platform = overrides.get("platform", "Google Meet")
    meeting.created_at = overrides.get("created_at", datetime(2026, 4, 26, tzinfo=timezone.utc))
    meeting.duration_minutes = overrides.get("duration_minutes", 45)
    meeting.summary = overrides.get("summary", "Team discussed sprint goals.")
    meeting.decisions = overrides.get("decisions", ["Approved Q3 plan"])
    meeting.action_items = overrides.get("action_items", [{"assignee": "Alice", "task": "Write spec", "deadline": "Friday"}])
    meeting.follow_up = overrides.get("follow_up", ["Schedule retro"])
    meeting.speaker_stats = overrides.get("speaker_stats", {"speakers": [{"speaker": "Alice"}]})
    meeting.transcript = overrides.get("transcript", "Alice: Let's go.")
    meeting.status = MagicMock()
    meeting.status.value = "completed"
    return meeting


def _excel_bytes() -> BytesIO:
    """Generate minimal valid xlsx bytes for mocking."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Title"])
    ws.append(["Test"])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _pdf_bytes() -> BytesIO:
    """Generate minimal valid PDF bytes for mocking."""
    buf = BytesIO()
    buf.write(b"%PDF-1.4 minimal test content")
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# T011 — Export all meetings endpoint
# ---------------------------------------------------------------------------

class TestExportAllMeetingsExcel:
    """T011: GET /api/export/meetings/excel integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200_with_xlsx_content_type(self) -> None:
        from src.main import app
        mock_meetings = [_make_mock_meeting()]

        with (
            patch("src.routes.export.Meeting") as MockMeeting,
            patch("src.routes.export.generate_all_meetings_excel", return_value=_excel_bytes()),
        ):
            mock_query = AsyncMock()
            mock_query.to_list = AsyncMock(return_value=mock_meetings)
            MockMeeting.find = MagicMock(return_value=mock_query)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/excel")

        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_returns_404_when_no_completed_meetings(self) -> None:
        from src.main import app

        with patch("src.routes.export.Meeting") as MockMeeting:
            mock_query = AsyncMock()
            mock_query.to_list = AsyncMock(return_value=[])
            MockMeeting.find = MagicMock(return_value=mock_query)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/excel")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_content_disposition_has_filename(self) -> None:
        from src.main import app
        mock_meetings = [_make_mock_meeting()]

        with (
            patch("src.routes.export.Meeting") as MockMeeting,
            patch("src.routes.export.generate_all_meetings_excel", return_value=_excel_bytes()),
        ):
            mock_query = AsyncMock()
            mock_query.to_list = AsyncMock(return_value=mock_meetings)
            MockMeeting.find = MagicMock(return_value=mock_query)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/excel")

        assert "filename=" in resp.headers.get("content-disposition", "")
        assert ".xlsx" in resp.headers.get("content-disposition", "")


# ---------------------------------------------------------------------------
# T017 — Export single meeting as PDF endpoint
# ---------------------------------------------------------------------------

class TestExportSingleMeetingPdf:
    """T017: GET /api/export/meetings/{id}/pdf integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200_with_pdf_content_type(self) -> None:
        from src.main import app
        mock_meeting = _make_mock_meeting()

        with (
            patch("src.routes.export.Meeting") as MockMeeting,
            patch("src.routes.export.generate_meeting_pdf", return_value=_pdf_bytes()),
        ):
            MockMeeting.get = AsyncMock(return_value=mock_meeting)
            MockMeeting.find = MagicMock()
            mock_meeting.status = MagicMock()
            mock_meeting.status.__eq__ = lambda self, other: True

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/507f1f77bcf86cd799439011/pdf")

        assert resp.status_code == 200
        assert "pdf" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_returns_404_when_meeting_not_found(self) -> None:
        from src.main import app

        with patch("src.routes.export.Meeting") as MockMeeting:
            MockMeeting.get = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/507f1f77bcf86cd799439011/pdf")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_content_disposition_has_pdf_filename(self) -> None:
        from src.main import app
        mock_meeting = _make_mock_meeting()

        with (
            patch("src.routes.export.Meeting") as MockMeeting,
            patch("src.routes.export.generate_meeting_pdf", return_value=_pdf_bytes()),
        ):
            MockMeeting.get = AsyncMock(return_value=mock_meeting)
            mock_meeting.status = MagicMock()
            mock_meeting.status.__eq__ = lambda self, other: True

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/507f1f77bcf86cd799439011/pdf")

        assert "filename=" in resp.headers.get("content-disposition", "")
        assert ".pdf" in resp.headers.get("content-disposition", "")


# ---------------------------------------------------------------------------
# T023 — Export single meeting as Excel endpoint
# ---------------------------------------------------------------------------

class TestExportSingleMeetingExcel:
    """T023: GET /api/export/meetings/{id}/excel integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200_with_xlsx_content_type(self) -> None:
        from src.main import app
        mock_meeting = _make_mock_meeting()

        with (
            patch("src.routes.export.Meeting") as MockMeeting,
            patch("src.routes.export.generate_single_meeting_excel", return_value=_excel_bytes()),
        ):
            MockMeeting.get = AsyncMock(return_value=mock_meeting)
            mock_meeting.status = MagicMock()
            mock_meeting.status.__eq__ = lambda self, other: True

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/507f1f77bcf86cd799439011/excel")

        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_returns_404_when_meeting_not_found(self) -> None:
        from src.main import app

        with patch("src.routes.export.Meeting") as MockMeeting:
            MockMeeting.get = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/507f1f77bcf86cd799439011/excel")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_content_disposition_has_xlsx_filename(self) -> None:
        from src.main import app
        mock_meeting = _make_mock_meeting()

        with (
            patch("src.routes.export.Meeting") as MockMeeting,
            patch("src.routes.export.generate_single_meeting_excel", return_value=_excel_bytes()),
        ):
            MockMeeting.get = AsyncMock(return_value=mock_meeting)
            mock_meeting.status = MagicMock()
            mock_meeting.status.__eq__ = lambda self, other: True

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/507f1f77bcf86cd799439011/excel")

        assert "filename=" in resp.headers.get("content-disposition", "")
        assert ".xlsx" in resp.headers.get("content-disposition", "")
