"""Database persistence helpers for output storage."""

from __future__ import annotations

import logging
from typing import Any

from modules.storage_errors import DatabaseWriteError
from modules._output_storage.types import (
    MeetingReportPayload,
    SaveableMeeting,
    TranscriptPayload,
)
from src.models.meeting import MeetingStatus

logger = logging.getLogger(__name__)


async def persist_meeting_report(
    meeting: SaveableMeeting,
    report: MeetingReportPayload | dict[str, Any],
    transcript: TranscriptPayload | dict[str, Any],
) -> None:
    """Map report/transcript fields onto a Meeting document and save it."""
    meeting.summary = report.get("summary")
    meeting.action_items = report.get("action_items", [])
    meeting.decisions = report.get("decisions", [])
    meeting.follow_up = report.get("follow_up", [])
    meeting.transcript = transcript.get("full_text")
    meeting.speaker_stats = report.get("speaker_stats")

    meeting.status = MeetingStatus.COMPLETED
    duration_seconds = float(transcript.get("duration_seconds", 0.0))
    meeting.duration_minutes = int(duration_seconds // 60)

    meeting_id = str(getattr(meeting, "id", "unknown"))
    logger.info(
        "[OS] Persisting meeting %r to MongoDB. duration_minutes=%d action_items=%d",
        meeting_id,
        meeting.duration_minutes,
        len(meeting.action_items),
    )

    try:
        await meeting.save()
    except Exception as exc:
        logger.error("[OS] Database write failed for meeting %r: %s", meeting_id, exc)
        raise DatabaseWriteError(meeting_id=meeting_id, cause=exc) from exc

    logger.info("[OS] Meeting %r saved successfully (status=COMPLETED).", meeting_id)
