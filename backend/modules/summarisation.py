"""
modules/summarisation.py
------------------------
Compatibility facade for the Summarisation & Analysis module.

The implementation lives under ``modules._summarisation`` so prompts, schemas,
LLM calling, parsing, speaker analytics, and orchestration can evolve
independently. The public import path is intentionally preserved:

    from modules.summarisation import Summarisation
"""

from __future__ import annotations

import openai

from config.settings import Config
from modules._summarisation.analytics import (
    analyse_participation as _analyse_participation,
)
from modules._summarisation.prompts import (
    SPEAKER_DETECTION_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
)
from modules._summarisation.schemas import (
    ActionItem,
    MeetingReportSchema,
    SpeakerDetectionSchema,
    SpeakerTurn,
)
from modules._summarisation.service import Summarisation as _Summarisation
from modules.llm_errors import (
    EmptyTranscriptError,
    LLMAPIError,
    LLMTimeoutError,
    ParseError,
)


class Summarisation(_Summarisation):
    """Compatibility subclass preserving the historical module patch surface."""

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        config: Config | None = None,
    ):
        super().__init__(
            model=model,
            temperature=temperature,
            config=config or Config(),
        )

    def _openai_module(self):
        return openai


__all__ = [
    "ActionItem",
    "MeetingReportSchema",
    "SpeakerDetectionSchema",
    "SpeakerTurn",
    "Summarisation",
]
