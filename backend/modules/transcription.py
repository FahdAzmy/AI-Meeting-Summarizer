"""
modules/transcription.py
------------------------
Compatibility facade for the Transcription module.

The implementation lives under ``modules._transcription`` so routing,
provider calls, normalisation, constants, and static types can evolve
separately. The public import path is intentionally preserved:

    from modules.transcription import Transcription
"""

from __future__ import annotations

import os
import time

import assemblyai as aai
import openai
import requests

from config.settings import Config
from modules._transcription.constants import (
    FALLBACK_ORDER as _FALLBACK_ORDER,
    MAX_AUDIO_BYTES as _MAX_AUDIO_BYTES,
    RETRY_ATTEMPTS as _RETRY_ATTEMPTS,
    _25_MB,
    _500_MB,
)
from modules._transcription.service import Transcription as _Transcription
from modules._transcription.types import TranscriptResult, TranscriptSegment
from modules.stt_errors import (
    AudioTooLargeError,
    NormalisationError,
    STTProviderError,
    STTRateLimitError,
    STTTimeoutError,
)


class Transcription(_Transcription):
    """Compatibility subclass preserving the historical module patch surface."""

    def __init__(
        self,
        provider: str = "whisper",
        language_code: str | None = "en",
        config: Config | None = None,
    ) -> None:
        super().__init__(
            provider=provider,
            language_code=language_code,
            config=config or Config(),
        )

    def _openai_module(self):
        return openai

    def _requests_module(self):
        return requests

    def _aai_module(self):
        return aai

    def _time_module(self):
        return time

    def _os_module(self):
        return os


__all__ = ["TranscriptResult", "TranscriptSegment", "Transcription"]
