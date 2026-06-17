"""
tests/unit/test_export.py
--------------------------
TDD test suite for the export API endpoints (post-SPEC-10 / SQLAlchemy).

Post-SPEC-10: endpoints use Depends(get_db) + select() instead of Beanie.
Tests override the FastAPI get_db dependency to inject a mock async session.
"""

from __future__ import annotations

import uuid
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
    from src.models.meeting import MeetingStatus
    meeting = MagicMock()
    meeting.id = overrides.get("id", uuid.uuid4())
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
    meeting.status = overrides.get("status", MeetingStatus.COMPLETED)
    return meeting


def _excel_bytes() -> BytesIO:
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
    buf = BytesIO()
    buf.write(b"%PDF-1.4 minimal test content")
    buf.seek(0)
    return buf


def _make_db_override(query_result):
    """
    Return a get_db dependency override that yields a mock async session.
    query_result: the value returned by session.execute(...).scalars().all()
                  OR scalar_one_or_none() depending on the test.
    """
    from src.helpers.db import get_db

    async def _fake_get_db():
        mock_session = AsyncMock()
        mock_exec_result = MagicMock()

        # Support both .scalars().all() and .scalar_one_or_none()
        mock_scalars = MagicMock()
        if isinstance(query_result, list):
            mock_scalars.all.return_value = query_result
            mock_exec_result.scalars.return_value = mock_scalars
            mock_exec_result.scalar_one_or_none.return_value = query_result[0] if query_result else None
        else:
            mock_exec_result.scalar_one_or_none.return_value = query_result
            mock_scalars.all.return_value = [query_result] if query_result else []
            mock_exec_result.scalars.return_value = mock_scalars

        mock_session.execute = AsyncMock(return_value=mock_exec_result)
        yield mock_session

    return {get_db: _fake_get_db}


# ---------------------------------------------------------------------------
# T011 — Export all meetings endpoint
# ---------------------------------------------------------------------------

class TestExportAllMeetingsExcel:
    """T011: GET /api/export/meetings/excel integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200_with_xlsx_content_type(self) -> None:
        from src.main import app
        mock_meetings = [_make_mock_meeting()]

        app.dependency_overrides = _make_db_override(mock_meetings)
        try:
            with patch("src.routes.export.generate_all_meetings_excel", return_value=_excel_bytes()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    resp = await ac.get("/api/export/meetings/excel")
        finally:
            app.dependency_overrides = {}

        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_returns_404_when_no_completed_meetings(self) -> None:
        from src.main import app

        app.dependency_overrides = _make_db_override([])
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/export/meetings/excel")
        finally:
            app.dependency_overrides = {}

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_content_disposition_has_filename(self) -> None:
        from src.main import app
        mock_meetings = [_make_mock_meeting()]

        app.dependency_overrides = _make_db_override(mock_meetings)
        try:
            with patch("src.routes.export.generate_all_meetings_excel", return_value=_excel_bytes()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    resp = await ac.get("/api/export/meetings/excel")
        finally:
            app.dependency_overrides = {}

        assert "filename=" in resp.headers.get("content-disposition", "")
        assert ".xlsx" in resp.headers.get("content-disposition", "")


# ---------------------------------------------------------------------------
# T017 — Export single meeting as PDF
# ---------------------------------------------------------------------------

class TestExportSingleMeetingPdf:
    """T017: GET /api/export/meetings/{id}/pdf integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200_with_pdf_content_type(self) -> None:
        from src.main import app
        meeting_id = uuid.uuid4()
        mock_meeting = _make_mock_meeting(id=meeting_id)

        app.dependency_overrides = _make_db_override(mock_meeting)
        try:
            with patch("src.routes.export.generate_meeting_pdf", return_value=_pdf_bytes()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    resp = await ac.get(f"/api/export/meetings/{meeting_id}/pdf")
        finally:
            app.dependency_overrides = {}

        assert resp.status_code == 200
        assert "pdf" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_returns_404_when_meeting_not_found(self) -> None:
        from src.main import app
        meeting_id = uuid.uuid4()

        app.dependency_overrides = _make_db_override(None)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get(f"/api/export/meetings/{meeting_id}/pdf")
        finally:
            app.dependency_overrides = {}

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_content_disposition_has_pdf_filename(self) -> None:
        from src.main import app
        meeting_id = uuid.uuid4()
        mock_meeting = _make_mock_meeting(id=meeting_id)

        app.dependency_overrides = _make_db_override(mock_meeting)
        try:
            with patch("src.routes.export.generate_meeting_pdf", return_value=_pdf_bytes()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    resp = await ac.get(f"/api/export/meetings/{meeting_id}/pdf")
        finally:
            app.dependency_overrides = {}

        assert "filename=" in resp.headers.get("content-disposition", "")
        assert ".pdf" in resp.headers.get("content-disposition", "")


# ---------------------------------------------------------------------------
# T023 — Export single meeting as Excel
# ---------------------------------------------------------------------------

class TestExportSingleMeetingExcel:
    """T023: GET /api/export/meetings/{id}/excel integration tests."""

    @pytest.mark.asyncio
    async def test_returns_200_with_xlsx_content_type(self) -> None:
        from src.main import app
        meeting_id = uuid.uuid4()
        mock_meeting = _make_mock_meeting(id=meeting_id)

        app.dependency_overrides = _make_db_override(mock_meeting)
        try:
            with patch("src.routes.export.generate_single_meeting_excel", return_value=_excel_bytes()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    resp = await ac.get(f"/api/export/meetings/{meeting_id}/excel")
        finally:
            app.dependency_overrides = {}

        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_returns_404_when_meeting_not_found(self) -> None:
        from src.main import app
        meeting_id = uuid.uuid4()

        app.dependency_overrides = _make_db_override(None)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get(f"/api/export/meetings/{meeting_id}/excel")
        finally:
            app.dependency_overrides = {}

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_content_disposition_has_xlsx_filename(self) -> None:
        from src.main import app
        meeting_id = uuid.uuid4()
        mock_meeting = _make_mock_meeting(id=meeting_id)

        app.dependency_overrides = _make_db_override(mock_meeting)
        try:
            with patch("src.routes.export.generate_single_meeting_excel", return_value=_excel_bytes()):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    resp = await ac.get(f"/api/export/meetings/{meeting_id}/excel")
        finally:
            app.dependency_overrides = {}

        assert "filename=" in resp.headers.get("content-disposition", "")
        assert ".xlsx" in resp.headers.get("content-disposition", "")
