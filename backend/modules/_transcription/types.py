"""Static transcript payload contracts."""

from __future__ import annotations

from typing import TypedDict


class TranscriptSegment(TypedDict):
    """A normalized transcription segment."""

    speaker: str | None
    start_time: float
    end_time: float
    text: str


class TranscriptResult(TypedDict):
    """Normalized transcription payload shared across the pipeline."""

    full_text: str
    segments: list[TranscriptSegment]
    language: str
    duration_seconds: float
    provider: str
    diarisation_available: bool
