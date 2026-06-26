"""
tests/unit/test_output_storage.py
----------------------------------
TDD test suite for the Output & Storage Module (post-SPEC-10 / PostgreSQL-only).

All external I/O is strictly mocked — no real DB, SMTP, or Sheets calls are made.
Post-SPEC-10: _store_to_database() writes via SQLAlchemy SessionLocal, not Beanie.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.output_storage import OutputStorage
from modules.storage_errors import (
    DatabaseWriteError,
    EmailDeliveryError,
    InvalidBackendError,
)


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

MOCK_REPORT: dict[str, Any] = {
    "summary": "## Meeting Summary\n\nTeam agreed on sprint goals.",
    "action_items": [
        {"assignee": "Alice", "task": "Write the spec", "deadline": "Friday"},
        {"assignee": "Bob",   "task": "Review the PR",  "deadline": "Monday"},
    ],
    "decisions": ["Sprint goals confirmed", "Release date set to Q3"],
    "follow_up": ["Schedule retro"],
    "speaker_stats": {
        "speakers": [
            {"speaker": "Alice", "total_speaking_time_sec": 120.0, "percentage_of_meeting": 60.0, "number_of_turns": 4},
            {"speaker": "Bob",   "total_speaking_time_sec": 80.0,  "percentage_of_meeting": 40.0, "number_of_turns": 3},
        ],
        "most_active_speaker": "Alice",
        "total_meeting_duration_sec": 200.0,
    },
}

MOCK_TRANSCRIPT: dict[str, Any] = {
    "full_text": "Alice: Write the spec. Bob: I'll review the PR.",
    "segments": [],
    "diarisation_available": False,
    "duration_seconds": 200.0,
}


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_mock_meeting(meeting_id: str | None = None) -> MagicMock:
    """Return a minimal meeting stub with a UUID id."""
    meeting = MagicMock()
    meeting.id = uuid.UUID(meeting_id) if meeting_id and "-" in meeting_id else uuid.uuid4()
    return meeting


def _make_stub_config(**overrides: Any) -> MagicMock:
    """Build a Config stub with sensible defaults for SMTP fields."""
    cfg = MagicMock()
    cfg.EMAIL_SENDER    = overrides.get("EMAIL_SENDER",    "bot@example.com")
    cfg.EMAIL_PASSWORD  = overrides.get("EMAIL_PASSWORD",  "test-password")
    cfg.EMAIL_SMTP_HOST = overrides.get("EMAIL_SMTP_HOST", "smtp.example.com")
    cfg.EMAIL_SMTP_PORT = overrides.get("EMAIL_SMTP_PORT", 587)
    return cfg


def _mock_session_local(mock_row: MagicMock):
    """Return (ctx_patch, mock_session) where the session's execute() returns mock_row."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_row
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    ctx = patch(
        "modules._output_storage.database.SessionLocal",
        return_value=mock_session_cm,
    )
    return ctx, mock_session


# ---------------------------------------------------------------------------
# T005 — Phase 2: Base scaffold & constructor validation
# ---------------------------------------------------------------------------

class TestOutputStorageScaffold:
    """T005: Verify OutputStorage instantiates correctly and validates its backend."""

    def test_instantiates_with_database_backend(self) -> None:
        storage = OutputStorage(backend="database", config=_make_stub_config())
        assert storage.backend == "database"

    def test_invalid_backend_raises_os004(self) -> None:
        with pytest.raises(InvalidBackendError) as exc_info:
            OutputStorage(backend="s3", config=_make_stub_config())
        assert "OS-004" in str(exc_info.value)
        assert "s3" in str(exc_info.value)

    def test_empty_backend_raises_os004(self) -> None:
        with pytest.raises(InvalidBackendError):
            OutputStorage(backend="", config=_make_stub_config())

    def test_config_smtp_values_wired_correctly(self) -> None:
        cfg = _make_stub_config(
            EMAIL_SENDER="sender@test.com",
            EMAIL_PASSWORD="secret",
            EMAIL_SMTP_HOST="smtp.test.com",
            EMAIL_SMTP_PORT=465,
        )
        storage = OutputStorage(backend="database", config=cfg)
        assert storage.email_sender   == "sender@test.com"
        assert storage.email_password == "secret"
        assert storage.smtp_host      == "smtp.test.com"
        assert storage.smtp_port      == 465

    def test_config_mongo_values_removed(self) -> None:
        """SPEC-10: OutputStorage must NOT expose mongo_uri or mongo_db attributes."""
        storage = OutputStorage(backend="database", config=_make_stub_config())
        assert not hasattr(storage, "mongo_uri"), "mongo_uri must be removed (SPEC-10)"
        assert not hasattr(storage, "mongo_db"),  "mongo_db must be removed (SPEC-10)"

    def test_default_backend_is_database(self) -> None:
        storage = OutputStorage(config=_make_stub_config())
        assert storage.backend == "database"

    async def test_store_to_database_is_async(self) -> None:
        import inspect
        storage = OutputStorage(config=_make_stub_config())
        assert inspect.iscoroutinefunction(storage._store_to_database)

    async def test_store_is_async(self) -> None:
        import inspect
        storage = OutputStorage(config=_make_stub_config())
        assert inspect.iscoroutinefunction(storage.store)

    async def test_async_mock_can_simulate_exception(self) -> None:
        mock_fn = AsyncMock(side_effect=RuntimeError("simulated failure"))
        with pytest.raises(RuntimeError, match="simulated failure"):
            await mock_fn()


# ---------------------------------------------------------------------------
# T006 / T007 — Phase 3: _store_to_database() (User Story 1)
# ---------------------------------------------------------------------------

class TestStoreToDatabaseUS1:
    """T006: _store_to_database() maps all report fields and commits once.
    T007: A DB commit failure must raise DatabaseWriteError (OS-003).

    Post-SPEC-10: uses SQLAlchemy SessionLocal; tests patch that session.
    """

    async def test_t006_save_awaited_exactly_once(self) -> None:
        """db.commit() must be called exactly once per call."""
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        ctx, mock_session = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        mock_session.commit.assert_awaited_once()

    async def test_t006_summary_mapped_to_meeting(self) -> None:
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert mock_row.summary == MOCK_REPORT["summary"]

    async def test_t006_action_items_mapped_to_meeting(self) -> None:
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert mock_row.action_items == MOCK_REPORT["action_items"]

    async def test_t006_decisions_mapped_to_meeting(self) -> None:
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert mock_row.decisions == MOCK_REPORT["decisions"]

    async def test_t006_transcript_full_text_mapped(self) -> None:
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert mock_row.transcript == MOCK_TRANSCRIPT["full_text"]

    async def test_t006_speaker_stats_mapped_when_present(self) -> None:
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert mock_row.speaker_stats == MOCK_REPORT["speaker_stats"]

    async def test_t006_speaker_stats_none_when_absent(self) -> None:
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        report_no_stats = {**MOCK_REPORT, "speaker_stats": None}
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, report_no_stats, MOCK_TRANSCRIPT)
        assert mock_row.speaker_stats is None

    async def test_t009_status_set_to_completed(self) -> None:
        from src.models.meeting import MeetingStatus
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert mock_row.status == MeetingStatus.COMPLETED

    async def test_t009_duration_minutes_calculated_correctly(self) -> None:
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        transcript_200s = {**MOCK_TRANSCRIPT, "duration_seconds": 200.0}
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, MOCK_REPORT, transcript_200s)
        assert mock_row.duration_minutes == 3  # int(200 // 60)

    async def test_t009_duration_zero_seconds(self) -> None:
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        transcript_0s = {**MOCK_TRANSCRIPT, "duration_seconds": 0.0}
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, MOCK_REPORT, transcript_0s)
        assert mock_row.duration_minutes == 0

    async def test_characterization_missing_report_fields_preserve_defaults(self) -> None:
        from src.models.meeting import MeetingStatus
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        ctx, _ = _mock_session_local(mock_row)
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            await storage._store_to_database(meeting, {}, {})
        assert mock_row.summary is None
        assert mock_row.action_items == []
        assert mock_row.decisions == []
        assert mock_row.follow_up == []
        assert mock_row.transcript is None
        assert mock_row.speaker_stats is None
        assert mock_row.status == MeetingStatus.COMPLETED
        assert mock_row.duration_minutes == 0

    # --- T007: error propagation ---

    async def test_t007_beanie_failure_raises_database_write_error(self) -> None:
        """If db.commit() raises, DatabaseWriteError (OS-003) must propagate."""
        mock_row = MagicMock()
        mock_row.id = uuid.uuid4()
        ctx, mock_session = _mock_session_local(mock_row)
        mock_session.commit = AsyncMock(side_effect=Exception("connection refused"))
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = mock_row.id
        with ctx:
            with pytest.raises(DatabaseWriteError) as exc_info:
                await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert "OS-003" in str(exc_info.value)

    async def test_t007_database_write_error_contains_meeting_id(self) -> None:
        """DatabaseWriteError message must reference the meeting id."""
        mock_row = MagicMock()
        meeting_id = uuid.uuid4()
        mock_row.id = meeting_id
        ctx, mock_session = _mock_session_local(mock_row)
        mock_session.commit = AsyncMock(side_effect=RuntimeError("timeout"))
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.id = meeting_id
        with ctx:
            with pytest.raises(DatabaseWriteError) as exc_info:
                await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert str(meeting_id) in str(exc_info.value)


# ---------------------------------------------------------------------------
# T010 / T011 — Phase 4: send_email() (User Story 2)
# ---------------------------------------------------------------------------

class TestSendEmailUS2:
    """T010: send_email() calls aiosmtplib.send() once per recipient.
    T011: A single SMTPException isolates failed recipient; rest succeed.
    """

    async def test_t010_send_called_once_per_recipient(self) -> None:
        recipients = ["alice@example.com", "bob@example.com", "carol@example.com"]
        storage = OutputStorage(config=_make_stub_config())

        with patch("modules.output_storage.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            result = await storage.send_email(recipients, MOCK_REPORT)

        assert mock_send.await_count == len(recipients)
        assert set(result["sent"]) == set(recipients)
        assert result["failed"] == []

    async def test_characterization_smtp_call_uses_configured_transport_args(self) -> None:
        storage = OutputStorage(
            config=_make_stub_config(
                EMAIL_SENDER="sender@test.com",
                EMAIL_PASSWORD="secret",
                EMAIL_SMTP_HOST="smtp.test.com",
                EMAIL_SMTP_PORT=2525,
            )
        )

        with patch("modules.output_storage.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await storage.send_email(["alice@example.com"], MOCK_REPORT)

        message = mock_send.await_args.args[0]
        kwargs = mock_send.await_args.kwargs

        assert message["Subject"] == "Your Meeting Summary \u2013 AI Meeting Summarizer"
        assert message["From"] == "sender@test.com"
        assert message["To"] == "alice@example.com"
        assert kwargs == {
            "hostname": "smtp.test.com",
            "port": 2525,
            "username": "sender@test.com",
            "password": "secret",
            "start_tls": True,
            "recipients": ["alice@example.com"],
        }

    async def test_t010_send_returns_sent_list(self) -> None:
        recipients = ["alice@example.com", "bob@example.com"]
        storage = OutputStorage(config=_make_stub_config())

        with patch("modules.output_storage.aiosmtplib.send", new_callable=AsyncMock):
            result = await storage.send_email(recipients, MOCK_REPORT)

        assert "alice@example.com" in result["sent"]
        assert "bob@example.com" in result["sent"]

    async def test_t010_empty_recipient_list_returns_empty_results(self) -> None:
        storage = OutputStorage(config=_make_stub_config())

        with patch("modules.output_storage.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            result = await storage.send_email([], MOCK_REPORT)

        mock_send.assert_not_awaited()
        assert result["sent"] == []
        assert result["failed"] == []

    async def test_t011_single_smtp_failure_isolated(self) -> None:
        from aiosmtplib import SMTPException

        recipients = ["alice@example.com", "bob@example.com", "carol@example.com"]
        storage = OutputStorage(config=_make_stub_config())

        async def _side_effect(*args: object, **kwargs: object) -> None:
            msg = args[0] if args else kwargs.get("message")
            to_header = str(msg["To"]) if msg and msg["To"] else ""
            if "bob@example.com" in to_header:
                raise SMTPException("mailbox unavailable")

        with patch("modules.output_storage.aiosmtplib.send", side_effect=_side_effect):
            result = await storage.send_email(recipients, MOCK_REPORT)

        assert "bob@example.com" in result["failed"]
        assert "alice@example.com" in result["sent"]
        assert "carol@example.com" in result["sent"]

    async def test_t011_failed_list_contains_failed_address(self) -> None:
        from aiosmtplib import SMTPException

        storage = OutputStorage(config=_make_stub_config())

        with patch(
            "modules.output_storage.aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=SMTPException("connection refused"),
        ):
            result = await storage.send_email(["alice@example.com"], MOCK_REPORT)

        assert "alice@example.com" in result["failed"]
        assert result["sent"] == []

    async def test_t011_global_smtp_failure_raises_email_delivery_error(self) -> None:
        from aiosmtplib import SMTPConnectError

        storage = OutputStorage(config=_make_stub_config())

        with patch(
            "modules.output_storage.aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=SMTPConnectError("could not connect to smtp.example.com:587"),
        ):
            with pytest.raises(EmailDeliveryError) as exc_info:
                await storage.send_email(["alice@example.com"], MOCK_REPORT)

        assert "OS-001" in str(exc_info.value)


# ---------------------------------------------------------------------------
# T018 — store() orchestrator
# ---------------------------------------------------------------------------

class TestStoreOrchestratorUS1US3:
    """T018: store() must always call _store_to_database()."""

    async def test_t018_store_always_calls_database(self) -> None:
        storage = OutputStorage(backend="database", config=_make_stub_config())
        storage._store_to_database = AsyncMock()

        await storage.store(_make_mock_meeting(), MOCK_REPORT, MOCK_TRANSCRIPT)

        storage._store_to_database.assert_awaited_once()

    async def test_t018_store_database_failure_propagates(self) -> None:
        storage = OutputStorage(backend="database", config=_make_stub_config())
        storage._store_to_database = AsyncMock(
            side_effect=DatabaseWriteError("mtg-1", Exception("boom"))
        )

        with pytest.raises(DatabaseWriteError):
            await storage.store(_make_mock_meeting(), MOCK_REPORT, MOCK_TRANSCRIPT)


# ---------------------------------------------------------------------------
# Characterization: HTML rendering contract
# ---------------------------------------------------------------------------

class TestEmailRenderingCharacterization:
    """Lock key HTML fragments so renderer extraction remains behavior-preserving."""

    async def test_full_report_renders_existing_dynamic_sections(self) -> None:
        storage = OutputStorage(config=_make_stub_config())
        html = await storage._format_email_body(MOCK_REPORT)

        assert "## Meeting Summary\n\nTeam agreed on sprint goals." in html
        assert "<li>Sprint goals confirmed</li>" in html
        assert "<li>Schedule retro</li>" in html
        assert "Speaker Highlights" in html
        assert "Most active: <strong>Alice</strong>" in html

    async def test_empty_report_renders_existing_fallback_fragments(self) -> None:
        storage = OutputStorage(config=_make_stub_config())
        html = await storage._format_email_body({})

        assert "No summary available." in html
        assert "<p><em>No decisions recorded.</em></p>" in html
        assert "<p><em>No action items recorded.</em></p>" in html
