"""Static-only typing contracts for output storage payloads."""

from __future__ import annotations

from typing import Any, Protocol, TypedDict

from src.models.meeting import MeetingStatus


class ActionItemPayload(TypedDict, total=False):
    assignee: str
    task: str
    deadline: str | None


class SpeakerPayload(TypedDict, total=False):
    speaker: str
    total_speaking_time_sec: float
    percentage_of_meeting: float
    number_of_turns: int


class SpeakerStatsPayload(TypedDict, total=False):
    speakers: list[SpeakerPayload]
    most_active_speaker: str
    total_meeting_duration_sec: float
    detection_method: str


class MeetingReportPayload(TypedDict, total=False):
    summary: str
    action_items: list[ActionItemPayload]
    decisions: list[str]
    follow_up: list[str]
    speaker_stats: SpeakerStatsPayload | None
    text_speaker_analysis: dict[str, Any] | None


class TranscriptPayload(TypedDict, total=False):
    full_text: str
    segments: list[dict[str, Any]]
    language: str
    duration_seconds: float
    provider: str
    diarisation_available: bool


class EmailSendResult(TypedDict):
    sent: list[str]
    failed: list[str]


class OutputStorageConfig(Protocol):
    EMAIL_SENDER: str
    EMAIL_PASSWORD: str
    EMAIL_SMTP_HOST: str
    EMAIL_SMTP_PORT: int


class SaveableMeeting(Protocol):
    """Protocol satisfied by any SQLAlchemy Meeting instance."""
    id: Any
    summary: str | None
    action_items: list[dict[str, Any]]
    decisions: list[str]
    follow_up: list[str]
    transcript: str | None
    speaker_stats: dict[str, Any] | None
    status: MeetingStatus
    duration_minutes: int | None
