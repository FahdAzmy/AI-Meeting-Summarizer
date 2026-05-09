"""Pydantic schemas for LLM summarisation responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """A single accountable task extracted from the meeting."""

    assignee: str
    task: str
    deadline: str | None = None


class MeetingReportSchema(BaseModel):
    """Strict Pydantic schema for the LLM JSON output."""

    summary: str = Field(..., description="Markdown-formatted meeting overview.")
    action_items: list[ActionItem] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    follow_up: list[str] = Field(default_factory=list)


class SpeakerTurn(BaseModel):
    """A single conversation turn identified by the LLM from transcript text."""

    speaker: str = Field(
        ...,
        description="Speaker name or label (e.g. 'Mr. Ahmed', 'Speaker 1').",
    )
    text: str = Field(..., description="The exact text spoken in this turn.")


class SpeakerDetectionSchema(BaseModel):
    """Strict Pydantic schema for LLM-based text speaker detection output."""

    turns: list[SpeakerTurn] = Field(default_factory=list)
    speakers_identified: int = Field(
        0,
        description="Total unique speakers detected.",
    )
