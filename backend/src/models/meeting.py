"""
src/models/meeting.py
----------------------
Beanie ODM document model for the Meeting collection in MongoDB.

This is the canonical persistence schema for a processed meeting.  All fields
map one-to-one with the ``MeetingReport`` dict produced by the Summarisation
module and the ``TranscriptResult`` dict from the Transcription module.

The document is intentionally sparse at creation time (status=PROCESSING,
summary=None, etc.) and is enriched in-place by ``OutputStorage._store_to_database()``.

Usage
-----
    from src.models.meeting import Meeting, MeetingStatus, ActionItem, SpeakerStats

    meeting = Meeting(title="Sprint Standup")
    await meeting.save()          # initial insert
    meeting.status = MeetingStatus.COMPLETED
    await meeting.save()          # update in-place
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document
from pydantic import Field


# ---------------------------------------------------------------------------
# Sub-document schemas (embedded in Meeting)
# ---------------------------------------------------------------------------


class MeetingStatus(str, Enum):
    """Pipeline lifecycle state for a Meeting document.

    States progress in order through the orchestrator pipeline:
        PENDING → JOINING → RECORDING → TRANSCRIBING → SUMMARISING
            → DELIVERING → COMPLETED
    Any state may transition to FAILED on a non-recoverable error.

    Legacy aliases
    --------------
    PROCESSING is retained for backward compatibility with documents
    written before the fine-grained states were introduced.
    """

    # ── Coarse legacy states (keep for backward compat) ──────────────────
    PENDING = "pending"        # Queued, not yet started
    PROCESSING = "processing"  # Generic "pipeline running" (pre-orchestrator)

    # ── Fine-grained orchestrator states ─────────────────────────────────
    JOINING = "joining"            # MeetingAccess joining the meeting room
    RECORDING = "recording"        # AudioCapture actively recording audio
    TRANSCRIBING = "transcribing"  # Transcription module converting audio→text
    SUMMARISING = "summarising"    # Summarisation module generating the report
    DELIVERING = "delivering"      # OutputStorage distributing results

    # ── Terminal states ───────────────────────────────────────────────────
    COMPLETED = "completed"  # All pipeline stages finished successfully
    FAILED = "failed"        # Non-recoverable pipeline error


class ActionItem(Document):
    """An accountable task extracted from the meeting transcript.

    Stored as an embedded sub-document array inside ``Meeting.action_items``.
    Not a top-level Beanie Document — used as a nested Pydantic model.
    """

    # Override to disable Beanie collection-level treatment for sub-docs.
    model_config = {"populate_by_name": True}  # type: ignore[assignment]

    assignee: str = Field(
        ..., description="Person responsible for completing the task."
    )
    task: str = Field(..., description="Description of the task.")
    deadline: Optional[str] = Field(None, description="Target completion date or None.")


class SpeakerStats(Document):
    """Speaker participation analytics embedded inside a Meeting document.

    Produced by either STT diarisation or LLM text-inference depending on
    the availability flag in the TranscriptResult.
    """

    model_config = {"populate_by_name": True}  # type: ignore[assignment]

    speakers: list[dict] = Field(default_factory=list)
    most_active_speaker: Optional[str] = None
    total_meeting_duration_sec: float = 0.0
    detection_method: Optional[str] = None  # "stt_diarisation" | "llm_inferred"


# ---------------------------------------------------------------------------
# Top-level Beanie Document
# ---------------------------------------------------------------------------


class Meeting(Document):
    """Primary MongoDB document for a single processed meeting session.

    Collection name: ``meetings``

    Lifecycle
    ---------
    1. Created with ``status=PROCESSING`` at pipeline start.
    2. Enriched by ``OutputStorage._store_to_database()`` after all AI stages.
    3. Persisted with ``status=COMPLETED`` and all analytical fields populated.
    """

    # ── Identity / Metadata ──────────────────────────────────────────────
    title: Optional[str] = Field(None, description="Human-readable meeting title.")
    meeting_link: Optional[str] = Field(
        None, description="Original meeting URL used to launch the pipeline."
    )
    session_id: Optional[str] = Field(
        None, description="Optional custom session identifier for tracking."
    )
    platform: Optional[str] = Field(
        None, description="Source platform (e.g. 'Zoom', 'Google Meet')."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the document was first created.",
    )

    # ── Pipeline lifecycle ───────────────────────────────────────────────
    status: MeetingStatus = Field(
        default=MeetingStatus.PROCESSING,
        description="Current pipeline lifecycle state.",
    )
    error_message: Optional[str] = Field(
        None, description="Human-readable error message if the meeting failed."
    )
    duration_minutes: Optional[int] = Field(
        None, description="Calculated meeting duration in whole minutes."
    )

    # ── Transcript ───────────────────────────────────────────────────────
    transcript: Optional[str] = Field(
        None,
        description="Full meeting transcript text (full_text from TranscriptResult).",
    )

    # ── Summarisation outputs ────────────────────────────────────────────
    summary: Optional[str] = Field(
        None, description="Markdown-formatted meeting summary from the LLM."
    )
    action_items: list[dict] = Field(
        default_factory=list,
        description="List of ActionItem dicts extracted by the LLM.",
    )
    decisions: list[str] = Field(
        default_factory=list,
        description="Key decisions reached during the meeting.",
    )
    follow_up: list[str] = Field(
        default_factory=list,
        description="Follow-up points to be addressed after the meeting.",
    )

    # ── Speaker analytics ────────────────────────────────────────────────
    speaker_stats: Optional[dict] = Field(
        None,
        description="Participation analytics (SpeakerStats dict or None if unavailable).",
    )

    class Settings:
        name = "meetings"  # MongoDB collection name
