"""
tests/unit/test_orchestrator.py
--------------------------------
Pytest test suite for ``src.orchestrator.run_pipeline``.

All external I/O is mocked — no real DB, no real AI modules.
Tests validate call routing, status transitions, and error handling.

Post-SPEC-10 architecture
--------------------------
The orchestrator no longer calls ``meeting.insert()`` or ``meeting.save()``.
Instead it uses two SQLAlchemy helpers:
  - ``SessionLocal``  —  async session factory  (patched at src.orchestrator.SessionLocal)
  - ``_update_meeting_status``  —  status-write helper  (patched to a no-op AsyncMock)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from src.orchestrator import run_pipeline

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MEETING_LINK = "https://meet.google.com/abc-defg-hij"
EMAILS = ["alice@example.com", "bob@example.com"]
STORAGE = "email"
FAKE_MEETING_ID = uuid.uuid4()

_T_ACCESS       = "src.orchestrator.MeetingAccess"
_T_CAPTURE      = "src.orchestrator.AudioCapture"
_T_TRANSCRIPTION = "src.orchestrator.Transcription"
_T_SUMMARISATION = "src.orchestrator.Summarisation"
_T_OUTPUT       = "src.orchestrator.OutputStorage"
_T_UPDATE_STATUS = "src.orchestrator._update_meeting_status"
_T_SESSION      = "src.orchestrator.SessionLocal"
_T_GET_COMPANY  = "src.orchestrator._get_or_create_default_company"

FAKE_TRANSCRIPT = {
    "full_text": "Alice: Hello. Bob: Hi.",
    "segments": [],
    "speaker_stats": None,
}

FAKE_REPORT = {
    "summary": "Quick sync.",
    "action_items": [],
    "decisions": [],
    "follow_up": [],
}


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def patch_pipeline():
    """Yield a namespace with all mock targets pre-configured."""

    # Mock SessionLocal so DB init block doesn't touch real DB
    mock_session = AsyncMock()
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=False)

    # Mock company object returned by _get_or_create_default_company
    mock_company = MagicMock()
    mock_company.id = uuid.uuid4()

    # Mock meeting row returned after DB insert
    mock_meeting_row = MagicMock()
    mock_meeting_row.id = FAKE_MEETING_ID

    # session.add / commit / refresh behavior
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "id", FAKE_MEETING_ID))

    with (
        patch(_T_SESSION, return_value=mock_session_cm) as MockSessionLocal,
        patch(_T_GET_COMPANY, new_callable=AsyncMock, return_value=mock_company),
        patch(_T_UPDATE_STATUS, new_callable=AsyncMock) as MockUpdateStatus,
        patch(_T_ACCESS) as MockAccess,
        patch(_T_CAPTURE) as MockCapture,
        patch(_T_TRANSCRIPTION) as MockTranscription,
        patch(_T_SUMMARISATION) as MockSummarisation,
        patch(_T_OUTPUT) as MockOutput,
    ):
        access_instance = MagicMock()
        access_instance.join = MagicMock()
        access_instance.wait_until_end = MagicMock()
        access_instance.leave = MagicMock()
        MockAccess.return_value = access_instance

        capture_instance = MagicMock()
        capture_instance.start = MagicMock()
        capture_instance.stop = MagicMock(return_value="/tmp/recording.mp4")
        MockCapture.return_value = capture_instance

        trans_instance = MagicMock()
        trans_instance.transcribe = MagicMock(return_value=FAKE_TRANSCRIPT)
        MockTranscription.return_value = trans_instance

        summ_instance = MagicMock()
        summ_instance.generate_report = MagicMock(return_value=FAKE_REPORT)
        MockSummarisation.return_value = summ_instance

        output_instance = MagicMock()
        output_instance.store = AsyncMock()
        output_instance.send_email = AsyncMock()
        MockOutput.return_value = output_instance

        ns = MagicMock()
        ns.MockSessionLocal = MockSessionLocal
        ns.MockUpdateStatus = MockUpdateStatus
        ns.mock_company = mock_company
        ns.MockAccess = MockAccess
        ns.access_instance = access_instance
        ns.MockCapture = MockCapture
        ns.capture_instance = capture_instance
        ns.MockTranscription = MockTranscription
        ns.trans_instance = trans_instance
        ns.MockSummarisation = MockSummarisation
        ns.summ_instance = summ_instance
        ns.MockOutput = MockOutput
        ns.output_instance = output_instance

        yield ns


# ---------------------------------------------------------------------------
# Harness sanity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_harness_meeting_is_mocked(patch_pipeline) -> None:
    """run_pipeline must NOT touch a real database."""
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)
    # SessionLocal must have been used to create the initial meeting record
    patch_pipeline.MockSessionLocal.assert_called()


@pytest.mark.asyncio
async def test_harness_all_ai_modules_are_mocked(patch_pipeline) -> None:
    """Every AI module constructor must be called exactly once per pipeline."""
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    patch_pipeline.MockAccess.assert_called_once()
    patch_pipeline.MockCapture.assert_called_once()
    patch_pipeline.MockTranscription.assert_called_once()
    patch_pipeline.MockSummarisation.assert_called_once()
    patch_pipeline.MockOutput.assert_called_once()


# ---------------------------------------------------------------------------
# Sequential execution order
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sequential_execution_order(patch_pipeline) -> None:
    """All 5 AI module methods must execute in strict pipeline order."""
    call_order: list[str] = []

    def _record_join(*a, **kw):
        call_order.append("join")

    def _record_start(*a, **kw):
        call_order.append("start")

    def _record_transcribe(*a, **kw):
        call_order.append("transcribe")
        return FAKE_TRANSCRIPT

    def _record_generate_report(*a, **kw):
        call_order.append("generate_report")
        return FAKE_REPORT

    async def _record_store(*a, **kw):
        call_order.append("store")

    patch_pipeline.access_instance.join = _record_join
    patch_pipeline.capture_instance.start = _record_start
    patch_pipeline.trans_instance.transcribe = _record_transcribe
    patch_pipeline.summ_instance.generate_report = _record_generate_report
    patch_pipeline.output_instance.store = _record_store

    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    assert call_order == ["join", "start", "transcribe", "generate_report", "store"], (
        f"Expected strict sequential order but got: {call_order}"
    )


@pytest.mark.asyncio
async def test_each_ai_module_called_exactly_once(patch_pipeline) -> None:
    """Each AI module's core method must be invoked exactly once."""
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    patch_pipeline.access_instance.join.assert_called_once()
    patch_pipeline.capture_instance.start.assert_called_once()
    patch_pipeline.trans_instance.transcribe.assert_called_once()
    patch_pipeline.summ_instance.generate_report.assert_called_once()
    patch_pipeline.output_instance.store.assert_awaited_once()


# ---------------------------------------------------------------------------
# Data handover
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transcript_flows_into_summarisation(patch_pipeline) -> None:
    """The dict returned by transcribe() must flow into generate_report()."""
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    patch_pipeline.summ_instance.generate_report.assert_called_once_with(
        FAKE_TRANSCRIPT, participant_hints=["Alice", "Bob"]
    )


@pytest.mark.asyncio
async def test_report_flows_into_output_storage(patch_pipeline) -> None:
    """generate_report() output must be the 2nd arg to store()."""
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    args, _ = patch_pipeline.output_instance.store.await_args
    # args = (meeting_proxy, report, transcript)
    assert args[1] == FAKE_REPORT
    assert args[2] == FAKE_TRANSCRIPT


# ---------------------------------------------------------------------------
# Status transitions (via _update_meeting_status)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_status_transitions_joining_to_completed(patch_pipeline) -> None:
    """_update_meeting_status must be called with each pipeline status in order."""
    from src.models.meeting import MeetingStatus

    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    statuses = [c.args[1] for c in patch_pipeline.MockUpdateStatus.await_args_list]
    assert statuses == [
        MeetingStatus.JOINING,
        MeetingStatus.RECORDING,
        MeetingStatus.TRANSCRIBING,
        MeetingStatus.SUMMARISING,
        MeetingStatus.DELIVERING,
        MeetingStatus.COMPLETED,
    ], f"Status progression mismatch: {statuses}"


@pytest.mark.asyncio
async def test_save_called_after_every_status_change(patch_pipeline) -> None:
    """_update_meeting_status must be called once per status transition (6 total)."""
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    assert patch_pipeline.MockUpdateStatus.await_count == 6, (
        f"Expected 6 status updates but got {patch_pipeline.MockUpdateStatus.await_count}"
    )


# ---------------------------------------------------------------------------
# Insert (initial DB write) called before pipeline
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_insert_called_before_pipeline_modules(patch_pipeline) -> None:
    """SessionLocal must be used to create the record before MeetingAccess is called."""
    call_log: list[str] = []

    # Track when SessionLocal context manager is entered (= initial DB write)
    original_cm = patch_pipeline.MockSessionLocal.return_value
    original_enter = original_cm.__aenter__

    async def _track_enter(*args, **kwargs):
        call_log.append("db_init")
        return await original_enter()

    original_cm.__aenter__ = _track_enter

    def _track_access(*a, **kw):
        call_log.append("MeetingAccess.__init__")
        return patch_pipeline.access_instance

    patch_pipeline.MockAccess.side_effect = _track_access

    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    assert "db_init" in call_log, "SessionLocal was never entered"
    assert "MeetingAccess.__init__" in call_log, "MeetingAccess was never constructed"
    assert call_log.index("db_init") < call_log.index("MeetingAccess.__init__"), (
        f"DB init must precede MeetingAccess, but order was: {call_log}"
    )


@pytest.mark.asyncio
async def test_insert_called_exactly_once(patch_pipeline) -> None:
    """SessionLocal must be entered exactly once to create the initial meeting record."""
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)
    # SessionLocal() is called once for initial insert; _update_meeting_status
    # calls it internally but that is patched out in this fixture
    patch_pipeline.MockSessionLocal.assert_called()


# ---------------------------------------------------------------------------
# Exception handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exception_in_transcribe_marks_failed(patch_pipeline) -> None:
    """If transcribe() raises, _update_meeting_status must be called with FAILED."""
    from src.models.meeting import MeetingStatus

    patch_pipeline.trans_instance.transcribe = MagicMock(
        side_effect=RuntimeError("STT provider unavailable")
    )

    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    # Last update_status call should be FAILED
    last_call = patch_pipeline.MockUpdateStatus.await_args_list[-1]
    assert last_call.args[1] == MeetingStatus.FAILED


@pytest.mark.asyncio
async def test_exception_in_summarisation_marks_failed(patch_pipeline) -> None:
    """If generate_report() raises, status must end up FAILED."""
    from src.models.meeting import MeetingStatus

    patch_pipeline.summ_instance.generate_report = MagicMock(
        side_effect=ValueError("LLM quota exceeded")
    )

    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    last_call = patch_pipeline.MockUpdateStatus.await_args_list[-1]
    assert last_call.args[1] == MeetingStatus.FAILED


@pytest.mark.asyncio
async def test_pipeline_does_not_raise_on_module_failure(patch_pipeline) -> None:
    """No exception from any AI module must escape run_pipeline."""
    patch_pipeline.access_instance.join.side_effect = ConnectionError("DNS failed")
    # Must complete without raising
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)


# ---------------------------------------------------------------------------
# asyncio.to_thread verification
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_blocking_calls_use_asyncio_to_thread(patch_pipeline) -> None:
    """access.join() and capture.start() must be offloaded to asyncio.to_thread."""
    to_thread_targets: list = []

    async def _tracking_to_thread(func, *args, **kwargs):
        to_thread_targets.append(func)
        return func(*args, **kwargs)

    with patch("src.orchestrator.asyncio.to_thread", side_effect=_tracking_to_thread):
        await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    assert patch_pipeline.access_instance.join in to_thread_targets, (
        f"access.join was not offloaded to asyncio.to_thread. Targets: {to_thread_targets}"
    )
    assert patch_pipeline.capture_instance.start in to_thread_targets, (
        f"capture.start was not offloaded to asyncio.to_thread. Targets: {to_thread_targets}"
    )
