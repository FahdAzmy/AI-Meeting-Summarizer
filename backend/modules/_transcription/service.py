"""Transcription router service implementation."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable

import assemblyai as aai
import openai
import requests

from config.settings import Config
from modules.stt_errors import (
    AudioTooLargeError,
    STTProviderError,
    STTRateLimitError,
    STTTimeoutError,
)
from modules._transcription.constants import (
    FALLBACK_ORDER,
    MAX_AUDIO_BYTES,
    RETRY_ATTEMPTS,
    SUPPORTED_PROVIDERS,
    _25_MB,
)
from modules._transcription.normalisers import (
    group_words_by_speaker,
    normalise,
    normalise_assemblyai,
    normalise_deepgram,
    normalise_whisper,
    segment_value,
)
from modules._transcription.providers import (
    transcribe_assemblyai,
    transcribe_deepgram,
    transcribe_whisper,
)
from modules._transcription.types import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class Transcription:
    """Router that delegates to a concrete STT provider."""

    SUPPORTED_PROVIDERS = set(SUPPORTED_PROVIDERS)

    def __init__(
        self,
        provider: str = "whisper",
        language_code: str | None = "en",
        config: Config | None = None,
    ) -> None:
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider '{provider}'. "
                f"Choose from: {self.SUPPORTED_PROVIDERS}"
            )
        self.provider: str = provider
        self.language_code: str | None = language_code
        cfg = config or Config()
        self.api_keys: dict[str, str] = {
            "whisper": cfg.WHISPER_API_KEY,
            "deepgram": cfg.DEEPGRAM_API_KEY,
            "assemblyai": cfg.ASSEMBLYAI_API_KEY,
        }
        self._whisper_client: Any | None = None
        self._dispatchers: dict[str, Callable[[str], dict[str, Any]]] = {
            "whisper": self._transcribe_whisper,
            "deepgram": self._transcribe_deepgram,
            "assemblyai": self._transcribe_assemblyai,
        }
        self._normalisers: dict[str, Callable[[dict[str, Any]], TranscriptResult]] = {
            "whisper": self._normalise_whisper,
            "deepgram": self._normalise_deepgram,
            "assemblyai": self._normalise_assemblyai,
        }
        logger.info(
            "Transcription router initialised with provider='%s', language_code=%s.",
            provider,
            language_code or "auto-detect",
        )

    def transcribe(self, audio_path: str) -> TranscriptResult:
        """Transcribe a local audio file, retrying and falling back as needed."""
        file_size = self._os_module().path.getsize(audio_path)
        max_bytes = MAX_AUDIO_BYTES.get(self.provider, _25_MB)
        if file_size > max_bytes:
            logger.error(
                "Audio file '%s' is %d bytes \u2013 exceeds %d byte limit for '%s'.",
                audio_path,
                file_size,
                max_bytes,
                self.provider,
            )
            raise AudioTooLargeError(audio_path, file_size)

        logger.info(
            "Starting transcription: provider='%s', file='%s', size=%d bytes.",
            self.provider,
            audio_path,
            file_size,
        )

        for attempt in range(RETRY_ATTEMPTS):
            try:
                t_start = self._time_module().monotonic()
                raw = self._dispatch(audio_path)
                result = self._normalise(raw)
                elapsed = self._time_module().monotonic() - t_start
                logger.info(
                    "Transcription complete: provider='%s', duration=%.2fs, "
                    "segments=%d, elapsed=%.3fs.",
                    self.provider,
                    result.get("duration_seconds", 0.0),
                    len(result.get("segments", [])),
                    elapsed,
                )
                return result

            except STTRateLimitError:
                fallback = FALLBACK_ORDER.get(self.provider)
                logger.warning(
                    "Rate limit (429) on '%s'; switching to '%s'.",
                    self.provider,
                    fallback,
                )
                self.provider = fallback
                attempt = 0

            except STTTimeoutError:
                sleep_secs = min(2**attempt * 5, 20)
                logger.warning(
                    "Timeout (408) on '%s', attempt %d/%d; sleeping %ds.",
                    self.provider,
                    attempt + 1,
                    RETRY_ATTEMPTS,
                    sleep_secs,
                )
                if attempt == RETRY_ATTEMPTS - 1:
                    raise STTTimeoutError(self.provider, RETRY_ATTEMPTS)
                self._time_module().sleep(sleep_secs)

        raise STTProviderError(self.provider, "All retry attempts exhausted.")

    def close(self) -> None:
        """Release reusable SDK clients when they expose a close hook."""
        close_method = getattr(self._whisper_client, "close", None)
        if callable(close_method):
            close_method()
        self._whisper_client = None

    def __enter__(self) -> "Transcription":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _dispatch(self, audio_path: str) -> dict[str, Any]:
        """Select and call the correct provider method."""
        dispatcher = self._dispatchers.get(self.provider)
        if dispatcher is not None:
            return dispatcher(audio_path)
        raise STTProviderError(self.provider, f"Unknown provider: {self.provider}")

    def _get_whisper_client(self) -> Any:
        """Return a per-instance OpenAI client for Whisper calls."""
        if self._whisper_client is None:
            self._whisper_client = self._openai_module().OpenAI(
                api_key=self.api_keys["whisper"]
            )
        return self._whisper_client

    def _transcribe_whisper(self, audio_path: str) -> dict[str, Any]:
        return transcribe_whisper(
            audio_path=audio_path,
            language_code=self.language_code,
            get_client=self._get_whisper_client,
            openai_module=self._openai_module(),
        )

    def _transcribe_deepgram(self, audio_path: str) -> dict[str, Any]:
        return transcribe_deepgram(
            audio_path=audio_path,
            language_code=self.language_code,
            api_key=self.api_keys["deepgram"],
            requests_module=self._requests_module(),
        )

    def _transcribe_assemblyai(self, audio_path: str) -> dict[str, Any]:
        return transcribe_assemblyai(
            audio_path=audio_path,
            language_code=self.language_code,
            api_key=self.api_keys["assemblyai"],
            aai_module=self._aai_module(),
        )

    def _normalise(self, raw: dict[str, Any]) -> TranscriptResult:
        return normalise(
            raw,
            current_provider=self.provider,
            normalisers=self._normalisers,
        )

    def _normalise_whisper(self, raw: dict[str, Any]) -> TranscriptResult:
        return normalise_whisper(raw)

    @staticmethod
    def _segment_value(segment: Any, key: str, default: Any) -> Any:
        return segment_value(segment, key, default)

    def _normalise_deepgram(self, raw: dict[str, Any]) -> TranscriptResult:
        return normalise_deepgram(raw)

    @staticmethod
    def _group_words_by_speaker(
        words: list[dict[str, Any]],
    ) -> list[TranscriptSegment]:
        return group_words_by_speaker(words)

    def _normalise_assemblyai(self, raw: dict[str, Any]) -> TranscriptResult:
        return normalise_assemblyai(raw)

    def _openai_module(self) -> Any:
        return openai

    def _requests_module(self) -> Any:
        return requests

    def _aai_module(self) -> Any:
        return aai

    def _time_module(self) -> Any:
        return time

    def _os_module(self) -> Any:
        return os
