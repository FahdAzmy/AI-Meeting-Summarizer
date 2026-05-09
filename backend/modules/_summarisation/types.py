"""Static-only typing contracts for summarisation payloads."""

from __future__ import annotations

from typing import Any, TypedDict


class TranscriptSegment(TypedDict, total=False):
    speaker: str | None
    start_time: float
    end_time: float
    start: float
    end: float
    text: str


class TranscriptPayload(TypedDict, total=False):
    full_text: str
    segments: list[TranscriptSegment]
    language: str
    duration_seconds: float
    provider: str
    diarisation_available: bool


class SpeakerStats(TypedDict, total=False):
    speakers: list[dict[str, Any]]
    most_active_speaker: str
    total_meeting_duration_sec: float
    detection_method: str


class MeetingReportPayload(TypedDict):
    summary: str
    action_items: list[dict[str, Any]]
    decisions: list[str]
    follow_up: list[str]
    speaker_stats: dict[str, Any] | None
    text_speaker_analysis: dict[str, Any] | None
