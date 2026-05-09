"""Parsing helpers for LLM summarisation responses."""

from __future__ import annotations

import json

from pydantic import ValidationError

from modules.llm_errors import ParseError
from modules._summarisation.schemas import MeetingReportSchema


def parse_meeting_report(raw_content: str) -> MeetingReportSchema:
    """Parse raw LLM JSON into the existing MeetingReportSchema contract."""
    try:
        payload = json.loads(raw_content)
        return MeetingReportSchema(**payload)
    except (json.JSONDecodeError, ValidationError, TypeError, KeyError) as exc:
        raise ParseError(
            message=f"LLM returned unparseable output: {raw_content[:200]!r}",
            cause=exc,
        ) from exc
