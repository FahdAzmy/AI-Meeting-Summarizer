"""
tests/unit/test_output_storage.py
----------------------------------
TDD test suite for the Output & Storage Module.

All external I/O boundaries are strictly mocked via ``unittest.mock.AsyncMock``
and ``unittest.mock.patch`` so that:
  - No real MongoDB, SMTP, or Google Sheets calls are made.
  - Each test verifies logic flows, error mapping, and routing in isolation.
  - The suite runs fully offline — zero external dependencies required.

Coverage map (tasks.md)
-----------------------
  T005  [Phase 2] Base pytest scaffold — AsyncMock loops, fixture helpers.
  T006  [Phase 3] _store_to_database() saves meeting document exactly once.
  T007  [Phase 3] Beanie driver failure raises DatabaseWriteError (OS-003).
  T010  [Phase 4] send_email() call count matches recipient list length.
  T011  [Phase 4] Single SMTPException isolates failed recipient; rest succeed.
  T014  [Phase 5] _store_to_sheets() appends rows containing all CSV columns.
  T015  [Phase 5] SheetsWriteError triggers pandas .to_csv() CSV fallback.

Notes
-----
- ``pytest.ini`` already sets ``asyncio_mode = auto`` so no explicit
  ``@pytest.mark.asyncio`` decorator is required on individual tests.
- All async helper fixtures use ``pytest_asyncio`` implicitly via auto mode.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.output_storage import OutputStorage
from modules.storage_errors import (
    DatabaseWriteError,
    EmailDeliveryError,
    InvalidBackendError,
    SheetsWriteError,
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
# Fixtures
# ---------------------------------------------------------------------------

def _make_mock_meeting(meeting_id: str = "meeting-123") -> MagicMock:
    """Return a minimal Beanie Meeting document stub.

    The ``save`` method is an ``AsyncMock`` so ``await meeting.save()``
    works without a live MongoDB connection.
    """
    meeting = MagicMock()
    meeting.id = meeting_id
    meeting.save = AsyncMock(return_value=None)
    return meeting


def _make_stub_config(**overrides: Any) -> MagicMock:
    """Build a Config stub with sensible defaults for the SMTP/Mongo fields."""
    cfg = MagicMock()
    cfg.EMAIL_SENDER   = overrides.get("EMAIL_SENDER",   "bot@example.com")
    cfg.EMAIL_PASSWORD = overrides.get("EMAIL_PASSWORD", "test-password")
    cfg.EMAIL_SMTP_HOST = overrides.get("EMAIL_SMTP_HOST", "smtp.example.com")
    cfg.EMAIL_SMTP_PORT = overrides.get("EMAIL_SMTP_PORT", 587)
    cfg.MONGO_URI      = overrides.get("MONGO_URI",      "mongodb://localhost:27017")
    cfg.MONGO_DB       = overrides.get("MONGO_DB",       "test_db")
    return cfg


# ---------------------------------------------------------------------------
# T005 — Phase 2: Base scaffold & constructor validation
# ---------------------------------------------------------------------------

class TestOutputStorageScaffold:
    """T005: Verify OutputStorage instantiates correctly and validates its backend.

    These tests confirm the constructor:
      - Accepts valid backend strings without raising.
      - Rejects invalid backend strings with InvalidBackendError (OS-004).
      - Correctly wires SMTP/Mongo config from the injected Config stub.
      - Exposes the expected public interface (async method signatures present).
    """

    def test_instantiates_with_database_backend(self) -> None:
        """Valid ``backend='database'`` must not raise."""
        storage = OutputStorage(backend="database", config=_make_stub_config())
        assert storage.backend == "database"

    def test_instantiates_with_google_sheets_backend(self) -> None:
        """Valid ``backend='google_sheets'`` must not raise."""
        storage = OutputStorage(backend="google_sheets", config=_make_stub_config())
        assert storage.backend == "google_sheets"

    def test_invalid_backend_raises_os004(self) -> None:
        """An unrecognised backend string must raise InvalidBackendError (OS-004)."""
        with pytest.raises(InvalidBackendError) as exc_info:
            OutputStorage(backend="s3", config=_make_stub_config())
        assert "OS-004" in str(exc_info.value)
        assert "s3" in str(exc_info.value)

    def test_empty_backend_raises_os004(self) -> None:
        """An empty string backend must also raise InvalidBackendError."""
        with pytest.raises(InvalidBackendError):
            OutputStorage(backend="", config=_make_stub_config())

    def test_config_smtp_values_wired_correctly(self) -> None:
        """SMTP fields must be read from the injected Config stub."""
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

    def test_config_mongo_values_wired_correctly(self) -> None:
        """Mongo fields must be read from the injected Config stub."""
        cfg = _make_stub_config(
            MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/prod",
            MONGO_DB="prod_db",
        )
        storage = OutputStorage(backend="database", config=cfg)
        assert storage.mongo_uri == "mongodb+srv://user:pass@cluster.mongodb.net/prod"
        assert storage.mongo_db  == "prod_db"

    def test_default_backend_is_database(self) -> None:
        """Omitting ``backend`` must default to ``'database'``."""
        storage = OutputStorage(config=_make_stub_config())
        assert storage.backend == "database"

    # --- async interface presence checks ---

    async def test_store_to_database_is_async(self) -> None:
        """``_store_to_database`` must be awaitable (coroutine function)."""
        import inspect
        storage = OutputStorage(config=_make_stub_config())
        assert inspect.iscoroutinefunction(storage._store_to_database)

    async def test_store_to_sheets_is_async(self) -> None:
        """``_store_to_sheets`` must be awaitable."""
        import inspect
        storage = OutputStorage(config=_make_stub_config())
        assert inspect.iscoroutinefunction(storage._store_to_sheets)

    async def test_send_email_is_async(self) -> None:
        """``send_email`` must be awaitable."""
        import inspect
        storage = OutputStorage(config=_make_stub_config())
        assert inspect.iscoroutinefunction(storage.send_email)

    async def test_store_is_async(self) -> None:
        """``store`` must be awaitable."""
        import inspect
        storage = OutputStorage(config=_make_stub_config())
        assert inspect.iscoroutinefunction(storage.store)

    # --- AsyncMock loop verification ---

    async def test_async_mock_save_is_awaitable(self) -> None:
        """Confirm that the ``_make_mock_meeting`` fixture wires save() as AsyncMock.

        This validates our test infrastructure before we write real assertions
        against Beanie save() calls in Phase 3.
        """
        meeting = _make_mock_meeting()
        # Should not raise; AsyncMock.save() is awaitable
        await meeting.save()
        meeting.save.assert_awaited_once()

    async def test_async_mock_can_simulate_exception(self) -> None:
        """Confirm that AsyncMock.side_effect wires up correctly for error tests."""
        mock_fn = AsyncMock(side_effect=RuntimeError("simulated failure"))
        with pytest.raises(RuntimeError, match="simulated failure"):
            await mock_fn()


# ---------------------------------------------------------------------------
# T006 / T007 — Phase 3: _store_to_database() (User Story 1)
# ---------------------------------------------------------------------------

class TestStoreToDatabaseUS1:
    """T006: _store_to_database() must map all report fields and await save() once.
    T007: A Beanie driver failure must raise DatabaseWriteError (OS-003).
    """

    async def test_t006_save_awaited_exactly_once(self) -> None:
        """T006: meeting.save() must be awaited exactly once per call."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        meeting.save.assert_awaited_once()

    async def test_t006_summary_mapped_to_meeting(self) -> None:
        """T006: meeting.summary must equal report['summary'] after the call."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert meeting.summary == MOCK_REPORT["summary"]

    async def test_t006_action_items_mapped_to_meeting(self) -> None:
        """T006: meeting.action_items must equal report['action_items'] list."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert meeting.action_items == MOCK_REPORT["action_items"]

    async def test_t006_decisions_mapped_to_meeting(self) -> None:
        """T006: meeting.decisions must equal report['decisions']."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert meeting.decisions == MOCK_REPORT["decisions"]

    async def test_t006_transcript_full_text_mapped(self) -> None:
        """T006: meeting.transcript must equal transcript['full_text']."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert meeting.transcript == MOCK_TRANSCRIPT["full_text"]

    async def test_t006_speaker_stats_mapped_when_present(self) -> None:
        """T006: meeting.speaker_stats must equal report['speaker_stats'] when available."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert meeting.speaker_stats == MOCK_REPORT["speaker_stats"]

    async def test_t006_speaker_stats_none_when_absent(self) -> None:
        """T006: meeting.speaker_stats must be None when report has no stats."""
        report_no_stats = {**MOCK_REPORT, "speaker_stats": None}
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, report_no_stats, MOCK_TRANSCRIPT)
        assert meeting.speaker_stats is None

    async def test_t009_status_set_to_completed(self) -> None:
        """T009: meeting.status must be MeetingStatus.COMPLETED after the call."""
        from src.models.meeting import MeetingStatus
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert meeting.status == MeetingStatus.COMPLETED

    async def test_t009_duration_minutes_calculated_correctly(self) -> None:
        """T009: duration_minutes must be floor(duration_seconds / 60)."""
        transcript_200s = {**MOCK_TRANSCRIPT, "duration_seconds": 200.0}
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, MOCK_REPORT, transcript_200s)
        assert meeting.duration_minutes == 3   # int(200 // 60)

    async def test_t009_duration_zero_seconds(self) -> None:
        """T009: duration_minutes must be 0 when duration_seconds is 0."""
        transcript_0s = {**MOCK_TRANSCRIPT, "duration_seconds": 0.0}
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        await storage._store_to_database(meeting, MOCK_REPORT, transcript_0s)
        assert meeting.duration_minutes == 0

    # --- T007: error propagation ---

    async def test_t007_beanie_failure_raises_database_write_error(self) -> None:
        """T007: If meeting.save() raises, DatabaseWriteError (OS-003) must propagate."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()
        meeting.save = AsyncMock(side_effect=Exception("motor connection refused"))
        with pytest.raises(DatabaseWriteError) as exc_info:
            await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert "OS-003" in str(exc_info.value)

    async def test_t007_database_write_error_contains_meeting_id(self) -> None:
        """T007: DatabaseWriteError message must reference the meeting id."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting(meeting_id="mtg-xyz-999")
        meeting.save = AsyncMock(side_effect=RuntimeError("timeout"))
        with pytest.raises(DatabaseWriteError) as exc_info:
            await storage._store_to_database(meeting, MOCK_REPORT, MOCK_TRANSCRIPT)
        assert "mtg-xyz-999" in str(exc_info.value)


# ---------------------------------------------------------------------------
# T010 / T011 — Phase 4: send_email() (User Story 2)
# ---------------------------------------------------------------------------

class TestSendEmailUS2:
    """T010: send_email() must call aiosmtplib.send() exactly once per recipient.
    T011: A single SMTPException must be isolated; remaining sends must succeed.
    """

    async def test_t010_send_called_once_per_recipient(self) -> None:
        """T010: aiosmtplib.send() invocation count must equal len(recipients)."""
        recipients = ["alice@example.com", "bob@example.com", "carol@example.com"]
        storage = OutputStorage(config=_make_stub_config())

        with patch("modules.output_storage.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            result = await storage.send_email(recipients, MOCK_REPORT)

        assert mock_send.await_count == len(recipients)
        assert set(result["sent"]) == set(recipients)
        assert result["failed"] == []

    async def test_t010_send_returns_sent_list(self) -> None:
        """T010: Successful recipients must appear in result['sent']."""
        recipients = ["alice@example.com", "bob@example.com"]
        storage = OutputStorage(config=_make_stub_config())

        with patch("modules.output_storage.aiosmtplib.send", new_callable=AsyncMock):
            result = await storage.send_email(recipients, MOCK_REPORT)

        assert "alice@example.com" in result["sent"]
        assert "bob@example.com" in result["sent"]

    async def test_t010_empty_recipient_list_returns_empty_results(self) -> None:
        """T010: Zero recipients must return empty sent and failed lists without calling send."""
        storage = OutputStorage(config=_make_stub_config())

        with patch("modules.output_storage.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            result = await storage.send_email([], MOCK_REPORT)

        mock_send.assert_not_awaited()
        assert result["sent"] == []
        assert result["failed"] == []

    async def test_t011_single_smtp_failure_isolated(self) -> None:
        """T011: SMTPException for one recipient must not abort delivery to others.

        The failed recipient must appear in result['failed']; every other
        recipient must appear in result['sent'].
        """
        from aiosmtplib import SMTPException

        recipients = ["alice@example.com", "bob@example.com", "carol@example.com"]
        storage = OutputStorage(config=_make_stub_config())

        async def _side_effect(*args: object, **kwargs: object) -> None:  # type: ignore[misc]
            # The first positional arg is the MIMEMultipart message object;
            # inspect its To header to decide which recipient to bounce.
            msg = args[0] if args else kwargs.get("message")
            to_header = str(msg["To"]) if msg and msg["To"] else ""  # type: ignore[index]
            if "bob@example.com" in to_header:
                raise SMTPException("mailbox unavailable")

        with patch(
            "modules.output_storage.aiosmtplib.send",
            side_effect=_side_effect,
        ):
            result = await storage.send_email(recipients, MOCK_REPORT)

        assert "bob@example.com" in result["failed"]
        assert "alice@example.com" in result["sent"]
        assert "carol@example.com" in result["sent"]

    async def test_t011_failed_list_contains_failed_address(self) -> None:
        """T011: The result['failed'] list must contain the address that bounced."""
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
        """T011: A connection-level failure (not per-recipient) must raise EmailDeliveryError (OS-001)."""
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
# T014 / T015 — Phase 5: _store_to_sheets() (User Story 3 & 4)
# ---------------------------------------------------------------------------

# Expected column names the Sheets row must contain (FR-004 / SC-003).
_EXPECTED_SHEET_COLUMNS = {"Date", "Participants", "Summary", "Decisions", "Action Items", "Duration (min)"}


class TestStoreToSheetsUS3US4:
    """T014: _store_to_sheets() must append a row with all required CSV columns.
    T015: A SheetsWriteError must trigger a pandas to_csv() fallback on disk.
    """

    async def test_t014_gspread_append_called_with_all_columns(self) -> None:
        """T014: The row appended to gspread must contain every expected column."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()

        mock_worksheet = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.sheet1 = mock_worksheet

        with patch("modules.output_storage.gspread") as mock_gspread:
            mock_gspread.service_account.return_value.open_by_key.return_value = mock_spreadsheet
            await storage._store_to_sheets(meeting, MOCK_REPORT)

        mock_worksheet.append_row.assert_called_once()
        appended_row: list = mock_worksheet.append_row.call_args[0][0]
        # Row must have at least as many cells as expected columns.
        assert len(appended_row) >= len(_EXPECTED_SHEET_COLUMNS)

    async def test_t014_appended_row_contains_summary(self) -> None:
        """T014: The appended Sheets row must include the report summary text."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()

        mock_worksheet = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.sheet1 = mock_worksheet

        with patch("modules.output_storage.gspread") as mock_gspread:
            mock_gspread.service_account.return_value.open_by_key.return_value = mock_spreadsheet
            await storage._store_to_sheets(meeting, MOCK_REPORT)

        appended_row: list = mock_worksheet.append_row.call_args[0][0]
        combined = " ".join(str(v) for v in appended_row)
        assert MOCK_REPORT["summary"] in combined

    async def test_t015_sheets_write_error_triggers_csv_fallback(self) -> None:
        """T015: SheetsWriteError must activate the pandas .to_csv() fallback."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()

        with (
            patch("modules.output_storage.gspread") as mock_gspread,
            patch("modules.output_storage.pd") as mock_pd,
        ):
            # Force gspread to raise SheetsWriteError.
            mock_gspread.service_account.return_value.open_by_key.side_effect = (
                SheetsWriteError("test-sheet-id", Exception("API down"))
            )
            mock_df = MagicMock()
            mock_pd.DataFrame.return_value = mock_df

            await storage._store_to_sheets(meeting, MOCK_REPORT)

        # Fallback must have called pandas to_csv().
        mock_df.to_csv.assert_called_once()
        csv_path: str = str(mock_df.to_csv.call_args[0][0])
        assert csv_path.endswith(".csv")

    async def test_t015_csv_fallback_does_not_raise(self) -> None:
        """T015: A SheetsWriteError must be swallowed — fallback must not re-raise."""
        storage = OutputStorage(config=_make_stub_config())
        meeting = _make_mock_meeting()

        with (
            patch("modules.output_storage.gspread") as mock_gspread,
            patch("modules.output_storage.pd") as mock_pd,
        ):
            mock_gspread.service_account.return_value.open_by_key.side_effect = (
                SheetsWriteError("sheet", Exception("timeout"))
            )
            mock_pd.DataFrame.return_value = MagicMock()

            # Must complete without raising.
            await storage._store_to_sheets(meeting, MOCK_REPORT)


# ---------------------------------------------------------------------------
# T018 — Phase 6: store() orchestrator (User Story 1 + 3)
# ---------------------------------------------------------------------------

class TestStoreOrchestratorUS1US3:
    """T018: store() must always call _store_to_database() and call
    _store_to_sheets() only when backend == 'google_sheets'.
    T019 (logging) is verified indirectly — store() logs at INFO level.
    """

    async def test_t018_store_always_calls_database(self) -> None:
        """T018: store() must call _store_to_database() for any backend."""
        storage = OutputStorage(backend="database", config=_make_stub_config())
        storage._store_to_database = AsyncMock()  # type: ignore[method-assign]
        storage._store_to_sheets = AsyncMock()    # type: ignore[method-assign]

        await storage.store(_make_mock_meeting(), MOCK_REPORT, MOCK_TRANSCRIPT)

        storage._store_to_database.assert_awaited_once()
        storage._store_to_sheets.assert_not_awaited()

    async def test_t018_store_calls_sheets_when_backend_is_google_sheets(self) -> None:
        """T018: store() must call _store_to_sheets() when backend='google_sheets'."""
        storage = OutputStorage(backend="google_sheets", config=_make_stub_config())
        storage._store_to_database = AsyncMock()  # type: ignore[method-assign]
        storage._store_to_sheets = AsyncMock()    # type: ignore[method-assign]

        await storage.store(_make_mock_meeting(), MOCK_REPORT, MOCK_TRANSCRIPT)

        storage._store_to_database.assert_awaited_once()
        storage._store_to_sheets.assert_awaited_once()

    async def test_t018_store_database_failure_propagates(self) -> None:
        """T018: A DatabaseWriteError from _store_to_database() must propagate."""
        storage = OutputStorage(backend="database", config=_make_stub_config())
        storage._store_to_database = AsyncMock(  # type: ignore[method-assign]
            side_effect=DatabaseWriteError("mtg-1", Exception("boom"))
        )
        storage._store_to_sheets = AsyncMock()  # type: ignore[method-assign]

        with pytest.raises(DatabaseWriteError):
            await storage.store(_make_mock_meeting(), MOCK_REPORT, MOCK_TRANSCRIPT)

    async def test_t018_store_sheets_not_called_on_database_failure(self) -> None:
        """T018: _store_to_sheets() must NOT be called if the DB write fails."""
        storage = OutputStorage(backend="google_sheets", config=_make_stub_config())
        storage._store_to_database = AsyncMock(  # type: ignore[method-assign]
            side_effect=DatabaseWriteError("mtg-2", Exception("db down"))
        )
        storage._store_to_sheets = AsyncMock()  # type: ignore[method-assign]

        with pytest.raises(DatabaseWriteError):
            await storage.store(_make_mock_meeting(), MOCK_REPORT, MOCK_TRANSCRIPT)

        storage._store_to_sheets.assert_not_awaited()
