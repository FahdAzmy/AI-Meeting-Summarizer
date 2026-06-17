"""Database persistence helpers for output storage (PostgreSQL/SQLAlchemy)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select

from modules.storage_errors import DatabaseWriteError
from modules._output_storage.types import (
    MeetingReportPayload,
    SaveableMeeting,
    TranscriptPayload,
)
from src.models.meeting import Meeting, MeetingStatus
from src.helpers.db import SessionLocal  # module-level — patchable in tests

logger = logging.getLogger(__name__)


async def persist_meeting_report(
    meeting: SaveableMeeting,
    report: MeetingReportPayload | dict[str, Any],
    transcript: TranscriptPayload | dict[str, Any],
    meeting_id: Any | None = None,
) -> None:
    """Map report/transcript fields onto a Meeting row and persist via SQLAlchemy."""

    # The meeting_id may be passed directly (preferred) or inferred from the object
    mid = meeting_id or getattr(meeting, "id", None)
    if mid is None:
        raise DatabaseWriteError(meeting_id="unknown", cause=ValueError("No meeting id"))

    if not isinstance(mid, uuid.UUID):
        try:
            mid = uuid.UUID(str(mid))
        except (ValueError, AttributeError) as exc:
            raise DatabaseWriteError(meeting_id=str(mid), cause=exc) from exc

    meeting_id_str = str(mid)
    logger.info(
        "[OS] Persisting meeting %r to PostgreSQL. action_items=%d",
        meeting_id_str,
        len(report.get("action_items", [])),
    )

    async with SessionLocal() as db:
        result = await db.execute(select(Meeting).where(Meeting.id == mid))
        row = result.scalar_one_or_none()
        if row is None:
            raise DatabaseWriteError(
                meeting_id=meeting_id_str,
                cause=ValueError(f"Meeting {meeting_id_str} not found in DB"),
            )

        row.summary = report.get("summary")
        row.action_items = report.get("action_items", [])
        row.decisions = report.get("decisions", [])
        row.follow_up = report.get("follow_up", [])
        row.transcript = transcript.get("full_text")
        row.speaker_stats = report.get("speaker_stats")
        row.status = MeetingStatus.COMPLETED

        duration_seconds = float(transcript.get("duration_seconds", 0.0))
        row.duration_minutes = int(duration_seconds // 60)

        try:
            await db.commit()
        except Exception as exc:
            logger.error("[OS] Database write failed for meeting %r: %s", meeting_id_str, exc)
            raise DatabaseWriteError(meeting_id=meeting_id_str, cause=exc) from exc

    logger.info("[OS] Meeting %r saved successfully (status=COMPLETED).", meeting_id_str)
