"""
tests/unit/test_orchestrator.py
--------------------------------
Pytest test suite for ``src.orchestrator.run_pipeline``.

Design contract
---------------
* **NO real I/O**.  Every AI module class and the Beanie ``Meeting``
  document are replaced by ``AsyncMock`` / ``MagicMock`` before each test.
* Tests exercise *routing logic* only — correct call order, correct
  ``MeetingStatus`` transitions, and correct error-handling paths.
* The ``patch_pipeline`` fixture sets up ALL mock targets in one place so
  individual tests stay short and readable.

Patched targets
---------------
  src.orchestrator.Meeting          – Beanie document (insert / save / status)
  src.orchestrator.MeetingStatus    – Status enum (real enum values)
  src.orchestrator.MeetingAccess    – meeting-room bot
  src.orchestrator.AudioCapture     – audio recorder
  src.orchestrator.Transcription    – STT engine
  src.orchestrator.Summarisation    – LLM summariser
  src.orchestrator.OutputStorage    – storage / distribution layer

Why patch at the orchestrator namespace?
----------------------------------------
``unittest.mock.patch`` replaces the *name* inside the target module, not
the original class definition.  Because ``orchestrator.py`` imports each
class at module level (``from modules.x import X``), patching
``src.orchestrator.X`` is the canonical and reliable approach.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from src.orchestrator import run_pipeline


# ---------------------------------------------------------------------------
# Constants used by multiple tests
# ---------------------------------------------------------------------------

MEETING_LINK = "https://meet.google.com/abc-defg-hij"
EMAILS = ["alice@example.com", "bob@example.com"]
STORAGE = "email"

# ── Patch target strings ────────────────────────────────────────────────────
_T_MEETING = "src.orchestrator.Meeting"
_T_STATUS = "src.orchestrator.MeetingStatus"
_T_ACCESS = "src.orchestrator.MeetingAccess"
_T_CAPTURE = "src.orchestrator.AudioCapture"
_T_TRANSCRIPTION = "src.orchestrator.Transcription"
_T_SUMMARISATION = "src.orchestrator.Summarisation"
_T_OUTPUT = "src.orchestrator.OutputStorage"

# ── Sample return payloads ──────────────────────────────────────────────────
FAKE_TRANSCRIPT: dict = {
    "full_text": "Alice: Hello. Bob: Hi.",
    "segments": [],
    "speaker_stats": None,
}

FAKE_REPORT: dict = {
    "summary": "Quick sync.",
    "action_items": [],
    "decisions": [],
    "follow_up": [],
}


# ---------------------------------------------------------------------------
# Shared fixture — full mock patch context
# ---------------------------------------------------------------------------


@pytest.fixture()
def patch_pipeline():
    """Yield a namespace with all mock targets pre-configured.

    The returned ``ns`` object exposes:

    ==================  ================================================
    Attribute           Description
    ==================  ================================================
    MockMeeting         Class mock for ``Meeting``
    meeting_instance    Instance returned by ``Meeting(...)``
    MockStatus          Mock for ``MeetingStatus`` enum
    MockAccess          Class mock for ``MeetingAccess``
    access_instance     Instance returned by ``MeetingAccess(...)``
    MockCapture         Class mock for ``AudioCapture``
    capture_instance    Instance returned by ``AudioCapture(...)``
    MockTranscription   Class mock for ``Transcription``
    trans_instance      Instance returned by ``Transcription(...)``
    MockSummarisation   Class mock for ``Summarisation``
    summ_instance       Instance returned by ``Summarisation(...)``
    MockOutput          Class mock for ``OutputStorage``
    output_instance     Instance returned by ``OutputStorage(...)``
    ==================  ================================================
    """
    with (
        patch(_T_MEETING) as MockMeeting,
        patch(_T_STATUS) as MockStatus,
        patch(_T_ACCESS) as MockAccess,
        patch(_T_CAPTURE) as MockCapture,
        patch(_T_TRANSCRIPTION) as MockTranscription,
        patch(_T_SUMMARISATION) as MockSummarisation,
        patch(_T_OUTPUT) as MockOutput,
    ):
        # ── Meeting instance ────────────────────────────────────────────────
        meeting_instance = MagicMock()
        meeting_instance.insert = AsyncMock()
        meeting_instance.save = AsyncMock()
        meeting_instance.id = "test-meeting-id-001"
        meeting_instance.status = None
        MockMeeting.return_value = meeting_instance

        # ── MeetingStatus — use real attribute names so assertions are clear
        MockStatus.JOINING = "joining"
        MockStatus.RECORDING = "recording"
        MockStatus.TRANSCRIBING = "transcribing"
        MockStatus.SUMMARISING = "summarising"
        MockStatus.DELIVERING = "delivering"
        MockStatus.COMPLETED = "completed"
        MockStatus.FAILED = "failed"

        # ── AI module instances ─────────────────────────────────────────────
        access_instance = MagicMock()
        access_instance.join = MagicMock()          # blocking sync method
        MockAccess.return_value = access_instance

        capture_instance = MagicMock()
        capture_instance.start = MagicMock()        # blocking sync method
        MockCapture.return_value = capture_instance

        trans_instance = MagicMock()
        # transcribe is a blocking sync method called via asyncio.to_thread
        trans_instance.transcribe = MagicMock(return_value=FAKE_TRANSCRIPT)
        MockTranscription.return_value = trans_instance

        summ_instance = MagicMock()
        # generate_report is a blocking sync method called via asyncio.to_thread
        summ_instance.generate_report = MagicMock(return_value=FAKE_REPORT)
        MockSummarisation.return_value = summ_instance

        output_instance = MagicMock()
        output_instance.store = AsyncMock()
        # send_email is also async — must be AsyncMock so it can be awaited
        output_instance.send_email = AsyncMock()
        MockOutput.return_value = output_instance

        # ── Namespace ───────────────────────────────────────────────────────
        ns = MagicMock()
        ns.MockMeeting = MockMeeting
        ns.meeting_instance = meeting_instance
        ns.MockStatus = MockStatus
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
# Phase 2 — T004: Harness sanity tests
# Verify the test infrastructure is correctly wired before any user-story
# tests are written.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_harness_meeting_is_mocked(patch_pipeline) -> None:
    """run_pipeline must NOT touch a real database.

    After a successful pipeline run ``Meeting.insert`` must be called
    exactly once, proving Beanie is fully intercepted.
    """
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    patch_pipeline.meeting_instance.insert.assert_called_once()


@pytest.mark.asyncio
async def test_harness_all_ai_modules_are_mocked(patch_pipeline) -> None:
    """Every AI module constructor must be called exactly once per pipeline.

    Confirms that none of the real heavy modules are instantiated and that
    the patch targets resolve correctly at runtime.
    """
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    patch_pipeline.MockAccess.assert_called_once()
    patch_pipeline.MockCapture.assert_called_once()
    patch_pipeline.MockTranscription.assert_called_once()
    patch_pipeline.MockSummarisation.assert_called_once()
    patch_pipeline.MockOutput.assert_called_once()


# ---------------------------------------------------------------------------
# Phase 3 — T005: Sequential execution verification  [P] [US1]
# Confirm that all 5 AI modules are called exactly once and in the correct
# sequential order: join → start → transcribe → generate_report → store.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sequential_execution_order(patch_pipeline) -> None:
    """All 5 AI module methods must execute in strict pipeline order.

    Uses a shared ``call_order`` list to record the actual invocation
    sequence, then asserts it matches the expected pipeline ordering.
    """
    call_order: list[str] = []

    # Instrument each mock to record when it is called
    original_join = patch_pipeline.access_instance.join
    original_start = patch_pipeline.capture_instance.start

    def _record_join(*a, **kw):
        call_order.append("join")
        return original_join(*a, **kw)

    def _record_start(*a, **kw):
        call_order.append("start")
        return original_start(*a, **kw)

    # transcribe and generate_report are sync (called via asyncio.to_thread)
    def _record_transcribe(*a, **kw):
        call_order.append("transcribe")
        return FAKE_TRANSCRIPT

    def _record_generate_report(*a, **kw):
        call_order.append("generate_report")
        return FAKE_REPORT

    # store is async (directly awaited by the orchestrator)
    async def _record_store(*a, **kw):
        call_order.append("store")

    patch_pipeline.access_instance.join = _record_join
    patch_pipeline.capture_instance.start = _record_start
    patch_pipeline.trans_instance.transcribe = _record_transcribe
    patch_pipeline.summ_instance.generate_report = _record_generate_report
    patch_pipeline.output_instance.store = _record_store

    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    assert call_order == [
        "join",
        "start",
        "transcribe",
        "generate_report",
        "store",
    ], f"Expected strict sequential order but got: {call_order}"


@pytest.mark.asyncio
async def test_each_ai_module_called_exactly_once(patch_pipeline) -> None:
    """Each AI module's core method must be invoked exactly once.

    This is the complementary assertion to the ordering test — it catches
    accidental double-invocations that the ordering test might miss if the
    duplicates happened to be adjacent.
    """
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    patch_pipeline.access_instance.join.assert_called_once()
    patch_pipeline.capture_instance.start.assert_called_once()
    patch_pipeline.trans_instance.transcribe.assert_called_once()
    patch_pipeline.summ_instance.generate_report.assert_called_once()
    patch_pipeline.output_instance.store.assert_called_once()


# ---------------------------------------------------------------------------
# Phase 3 — T006: Data handover verification  [P] [US1]
# Confirm that the output of transcribe() is passed as input to
# generate_report(), and the output of generate_report() is passed to store().
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transcript_flows_into_summarisation(patch_pipeline) -> None:
    """The dict returned by ``transcribe()`` must be the first positional
    argument passed to ``generate_report()``.

    This proves data is not silently dropped between pipeline stages.
    """
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    # generate_report is called synchronously via asyncio.to_thread — use assert_called_once_with
    patch_pipeline.summ_instance.generate_report.assert_called_once_with(
        FAKE_TRANSCRIPT
    )


@pytest.mark.asyncio
async def test_report_flows_into_output_storage(patch_pipeline) -> None:
    """The dict returned by ``generate_report()`` must be the first
    positional argument passed to ``store()``.

    This proves the LLM report is handed off to storage without mutation.
    """
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    # store is called as: await output.store(meeting, report, transcript)
    # Verify the report (2nd arg) and transcript (3rd arg) flow through correctly.
    patch_pipeline.output_instance.store.assert_awaited_once_with(
        patch_pipeline.meeting_instance, FAKE_REPORT, FAKE_TRANSCRIPT
    )


# ===========================================================================
# Phase 4 — T009: Status transition tracking  [P] [US2]
# Verify that meeting.status tracks through every pipeline stage in the
# correct order: JOINING → RECORDING → TRANSCRIBING → SUMMARISING →
# DELIVERING → COMPLETED.
# ===========================================================================


@pytest.mark.asyncio
async def test_status_transitions_joining_to_completed(patch_pipeline) -> None:
    """meeting.status must cycle through every orchestrator state in order.

    We capture every value assigned to ``meeting.status`` and assert the
    full ordered sequence matches the expected pipeline progression.
    """
    statuses_seen: list[str] = []

    # Use a property-like side_effect on __setattr__ to capture status writes
    real_meeting = patch_pipeline.meeting_instance

    original_setattr = type(real_meeting).__setattr__

    def _tracking_setattr(self, name, value):
        if name == "status":
            statuses_seen.append(value)
        original_setattr(self, name, value)

    type(real_meeting).__setattr__ = _tracking_setattr

    try:
        await run_pipeline(MEETING_LINK, EMAILS, STORAGE)
    finally:
        type(real_meeting).__setattr__ = original_setattr

    assert statuses_seen == [
        "joining",
        "recording",
        "transcribing",
        "summarising",
        "delivering",
        "completed",
    ], f"Status progression mismatch: {statuses_seen}"


@pytest.mark.asyncio
async def test_save_called_after_every_status_change(patch_pipeline) -> None:
    """``meeting.save()`` must be called once per status change.

    The pipeline has 6 status transitions (JOINING through COMPLETED),
    so ``save`` must be called exactly 6 times on a successful run.
    """
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    assert patch_pipeline.meeting_instance.save.await_count == 6, (
        f"Expected 6 save() calls but got "
        f"{patch_pipeline.meeting_instance.save.await_count}"
    )


# ===========================================================================
# Phase 4 — T010: Insert called before pipeline loop  [P] [US2]
# Verify that meeting.insert() is called exactly once, and that it
# happens before any AI module is invoked.
# ===========================================================================


@pytest.mark.asyncio
async def test_insert_called_before_pipeline_modules(patch_pipeline) -> None:
    """``meeting.insert()`` must execute before any AI module constructor.

    Uses a shared order list to prove ``insert`` precedes ``MeetingAccess``.
    """
    call_log: list[str] = []

    patch_pipeline.meeting_instance.insert = AsyncMock(
        side_effect=lambda: call_log.append("insert")
    )

    original_access_init = patch_pipeline.MockAccess.side_effect

    def _track_access(*a, **kw):
        call_log.append("MeetingAccess.__init__")
        return patch_pipeline.access_instance

    patch_pipeline.MockAccess.side_effect = _track_access

    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    assert "insert" in call_log, "insert() was never called"
    assert "MeetingAccess.__init__" in call_log, "MeetingAccess was never constructed"
    assert call_log.index("insert") < call_log.index("MeetingAccess.__init__"), (
        f"insert() must precede MeetingAccess but order was: {call_log}"
    )


@pytest.mark.asyncio
async def test_insert_called_exactly_once(patch_pipeline) -> None:
    """The meeting document must be inserted into the database exactly once."""
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    patch_pipeline.meeting_instance.insert.assert_awaited_once()


# ===========================================================================
# Phase 5 — T012: Exception triggers FAILED status  [P] [US3]
# Mock transcribe() to throw an Exception and verify the orchestrator
# catches it, sets status=FAILED, and persists the failure to the DB.
# ===========================================================================


@pytest.mark.asyncio
async def test_exception_in_transcribe_marks_failed(patch_pipeline) -> None:
    """If ``transcribe()`` raises, the meeting must end up FAILED.

    The orchestrator's top-level ``try/except`` must catch the error,
    set ``meeting.status = MeetingStatus.FAILED``, and call ``save()``.
    """
    patch_pipeline.trans_instance.transcribe = MagicMock(
        side_effect=RuntimeError("STT provider unavailable")
    )

    # Pipeline must NOT raise — the exception is swallowed internally
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    # The last status written should be FAILED
    assert patch_pipeline.meeting_instance.status == "failed", (
        f"Expected FAILED but got {patch_pipeline.meeting_instance.status}"
    )


@pytest.mark.asyncio
async def test_exception_in_summarisation_marks_failed(patch_pipeline) -> None:
    """If ``generate_report()`` raises, the meeting must end up FAILED."""
    patch_pipeline.summ_instance.generate_report = MagicMock(
        side_effect=ValueError("LLM quota exceeded")
    )

    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    assert patch_pipeline.meeting_instance.status == "failed"


@pytest.mark.asyncio
async def test_pipeline_does_not_raise_on_module_failure(patch_pipeline) -> None:
    """No exception from any AI module must escape ``run_pipeline``.

    The FastAPI worker thread must stay healthy regardless of pipeline
    failures — the orchestrator catches everything internally.
    """
    patch_pipeline.access_instance.join.side_effect = ConnectionError("DNS failed")

    # Must complete without raising
    await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    assert patch_pipeline.meeting_instance.status == "failed"


# ===========================================================================
# Phase 5 — T013: asyncio.to_thread verification  [P] [US3]
# Verify that blocking calls (access.join, capture.start) are offloaded
# to a thread pool via asyncio.to_thread.
# ===========================================================================


@pytest.mark.asyncio
async def test_blocking_calls_use_asyncio_to_thread(patch_pipeline) -> None:
    """``access.join()`` and ``capture.start()`` must be wrapped in
    ``asyncio.to_thread`` to avoid blocking the event loop.

    We patch ``asyncio.to_thread`` itself and verify it is called with
    the correct target functions (the mock instances' methods).
    """
    to_thread_targets: list = []

    async def _tracking_to_thread(func, *args, **kwargs):
        to_thread_targets.append(func)
        # Execute synchronously — the real to_thread would run in a thread,
        # but for unit-testing the routing logic this is sufficient.
        return func(*args, **kwargs)

    with patch("src.orchestrator.asyncio.to_thread", side_effect=_tracking_to_thread):
        await run_pipeline(MEETING_LINK, EMAILS, STORAGE)

    # The orchestrator should have offloaded access.join and capture.start
    assert patch_pipeline.access_instance.join in to_thread_targets, (
        f"access.join was not offloaded to asyncio.to_thread. Targets: {to_thread_targets}"
    )
    assert patch_pipeline.capture_instance.start in to_thread_targets, (
        f"capture.start was not offloaded to asyncio.to_thread. Targets: {to_thread_targets}"
    )
