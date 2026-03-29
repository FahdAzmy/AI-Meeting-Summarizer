"""
modules/transcription.py
------------------------
Transcription Module – Router Strategy over Speech-to-Text APIs.

Supported providers
-------------------
  * whisper     – OpenAI Whisper-1 (via openai Python SDK)
  * deepgram    – Deepgram Nova (via HTTP REST, diarization=true)
  * assemblyai  – AssemblyAI (async polling via assemblyai SDK)

Output schema  (TranscriptResult)
----------------------------------
{
    "full_text":             str,
    "segments":              [{"speaker": str|None, "start_time": float,
                               "end_time": float, "text": str}],
    "language":              str,          # ISO 639-1
    "duration_seconds":      float,
    "provider":              str,
    "diarisation_available": bool,
}

Error taxonomy (see modules/stt_errors.py)
------------------------------------------
  TR-001  STTProviderError     – HTTP 5xx / unclassified SDK error
  TR-002  STTTimeoutError      – HTTP 408 after all retries exhausted
  TR-003  STTRateLimitError    – HTTP 429 (caller should switch provider)
  TR-004  AudioTooLargeError   – file exceeds provider limit (25 MB whisper / 500 MB others)
  TR-005  NormalisationError   – raw response missing expected keys
"""

from __future__ import annotations

import logging
import os
import mimetypes
import time
from typing import Any

import assemblyai as aai
import openai
import requests

from config.settings import Config
from modules.stt_errors import (
    AudioTooLargeError,
    NormalisationError,
    STTProviderError,
    STTRateLimitError,
    STTTimeoutError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_AUDIO_BYTES: dict[str, int] = {
    "whisper": 25 * 1024 * 1024,     # 25 MB  – OpenAI hard limit
    "deepgram": 500 * 1024 * 1024,   # 500 MB – Deepgram supports up to 2 GB
    "assemblyai": 500 * 1024 * 1024, # 500 MB – AssemblyAI supports large files
}
_RETRY_ATTEMPTS: int = 3
_FALLBACK_ORDER: dict[str, str] = {
    "whisper": "deepgram",
    "deepgram": "assemblyai",
    "assemblyai": "whisper",
}

# Type alias – mirrors the data-model.md spec exactly
TranscriptResult = dict[str, Any]


# ---------------------------------------------------------------------------
# Main router class
# ---------------------------------------------------------------------------


class Transcription:
    """Abstract router that delegates to a concrete STT provider.

    Parameters
    ----------
    provider : str
        Starting provider: ``"whisper"`` (default), ``"deepgram"``,
        or ``"assemblyai"``.
    """

    SUPPORTED_PROVIDERS = {"whisper", "deepgram", "assemblyai"}

    def __init__(self, provider: str = "whisper") -> None:
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider '{provider}'. "
                f"Choose from: {self.SUPPORTED_PROVIDERS}"
            )
        self.provider: str = provider
        cfg = Config()
        self.api_keys: dict[str, str] = {
            "whisper": cfg.WHISPER_API_KEY,
            "deepgram": cfg.DEEPGRAM_API_KEY,
            "assemblyai": cfg.ASSEMBLYAI_API_KEY,
        }
        logger.info("Transcription router initialised with provider='%s'.", provider)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transcribe(self, audio_path: str) -> TranscriptResult:
        """Transcribe a local audio file, retrying and falling back as needed.

        Parameters
        ----------
        audio_path : str
            Absolute or relative path to the WAV (or other) audio file.

        Returns
        -------
        TranscriptResult
            Normalised transcription dict conforming to the data-model schema.

        Raises
        ------
        AudioTooLargeError
            If the file exceeds the provider's size limit before any network I/O.
        STTTimeoutError
            After _RETRY_ATTEMPTS consecutive 408 responses.
        STTProviderError
            On unrecoverable 5xx or SDK errors with no fallback available.
        """
        # ── TR-004: provider-specific file-size guard ────────────────────
        file_size = os.path.getsize(audio_path)
        max_bytes = _MAX_AUDIO_BYTES.get(self.provider, 25 * 1024 * 1024)
        if file_size > max_bytes:
            logger.error(
                "Audio file '%s' is %d bytes – exceeds %d byte limit for '%s'.",
                audio_path, file_size, max_bytes, self.provider,
            )
            raise AudioTooLargeError(audio_path, file_size)

        logger.info(
            "Starting transcription: provider='%s', file='%s', size=%d bytes.",
            self.provider,
            audio_path,
            file_size,
        )

        # ── Main dispatch + fallback loop ────────────────────────────────
        for attempt in range(_RETRY_ATTEMPTS):
            try:
                t_start = time.monotonic()
                raw = self._dispatch(audio_path)
                result = self._normalise(raw)
                elapsed = time.monotonic() - t_start
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
                # TR-003: switch provider immediately, no sleep
                fallback = _FALLBACK_ORDER.get(self.provider)
                logger.warning(
                    "Rate limit (429) on '%s'; switching to '%s'.",
                    self.provider,
                    fallback,
                )
                self.provider = fallback
                attempt = 0  # reset counter for new provider

            except STTTimeoutError:
                # TR-002: exponential backoff
                sleep_secs = min(2 ** attempt * 5, 20)
                logger.warning(
                    "Timeout (408) on '%s', attempt %d/%d; sleeping %ds.",
                    self.provider,
                    attempt + 1,
                    _RETRY_ATTEMPTS,
                    sleep_secs,
                )
                if attempt == _RETRY_ATTEMPTS - 1:
                    raise STTTimeoutError(self.provider, _RETRY_ATTEMPTS)
                time.sleep(sleep_secs)

        # Should not reach here under normal flow
        raise STTProviderError(self.provider, "All retry attempts exhausted.")

    # ------------------------------------------------------------------
    # Internal dispatcher
    # ------------------------------------------------------------------

    def _dispatch(self, audio_path: str) -> dict[str, Any]:
        """Select and call the correct provider method."""
        if self.provider == "whisper":
            return self._transcribe_whisper(audio_path)
        if self.provider == "deepgram":
            return self._transcribe_deepgram(audio_path)
        if self.provider == "assemblyai":
            return self._transcribe_assemblyai(audio_path)
        raise STTProviderError(self.provider, f"Unknown provider: {self.provider}")

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    def _transcribe_whisper(self, audio_path: str) -> dict[str, Any]:
        """Upload audio to OpenAI Whisper-1 and return the raw response dict.

        Parameters
        ----------
        audio_path : str
            Path to the audio file to transcribe.

        Returns
        -------
        dict
            Raw OpenAI verbose_json response.

        Raises
        ------
        STTTimeoutError
            On HTTP 408 from the OpenAI API.
        STTRateLimitError
            On HTTP 429 from the OpenAI API.
        STTProviderError
            On any other HTTP error or SDK exception.
        """
        logger.info("Calling OpenAI Whisper: file='%s'.", audio_path)
        try:
            client = openai.OpenAI(api_key=self.api_keys["whisper"])
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
            # SDK returns a Transcription object; convert to dict for normalisation
            raw: dict[str, Any] = {
                "text": response.text,
                "segments": response.segments or [],
                "language": getattr(response, "language", "en"),
                "duration": getattr(response, "duration", 0.0),
                "_provider": "whisper",
            }
            logger.debug("Whisper raw response received: %d segment(s).", len(raw["segments"]))
            return raw

        except openai.APIStatusError as exc:
            status = exc.status_code
            if status == 408:
                raise STTTimeoutError("whisper", 1) from exc
            if status == 429:
                raise STTRateLimitError("whisper") from exc
            raise STTProviderError("whisper", str(exc)) from exc
        except Exception as exc:
            raise STTProviderError("whisper", str(exc)) from exc

    def _transcribe_deepgram(self, audio_path: str) -> dict[str, Any]:
        """Upload audio to Deepgram Nova with speaker diarization enabled.

        Uses the Deepgram REST API directly via ``requests`` so that we can
        intercept ``requests.exceptions.HTTPError`` uniformly for retry logic.

        Returns
        -------
        dict
            Raw Deepgram JSON response body.

        Raises
        ------
        STTTimeoutError
            On HTTP 408.
        STTRateLimitError
            On HTTP 429.
        STTProviderError
            On other HTTP errors or network exceptions.
        """
        url = "https://api.deepgram.com/v1/listen?model=nova-3&diarize=true&punctuate=true&detect_language=true&smart_format=true"
        # Dynamically determine content type from file extension (e.g. .mp4 -> video/mp4)
        mime_type, _ = mimetypes.guess_type(audio_path)
        content_type = mime_type if mime_type else "audio/wav"
        
        headers = {
            "Authorization": f"Token {self.api_keys['deepgram']}",
            "Content-Type": content_type,
        }
        logger.info("Calling Deepgram: file='%s' (Content-Type: %s)", audio_path, content_type)
        try:
            with open(audio_path, "rb") as f:
                payload = f.read()
                
            resp = requests.post(
                url, 
                headers=headers, 
                data=payload, # Send bytes directly to enforce Content-Length
                timeout=120
            )
            resp.raise_for_status()
            raw = resp.json()
            raw["_provider"] = "deepgram"
            return raw

        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            if status == 408:
                raise STTTimeoutError("deepgram", 1) from exc
            if status == 429:
                raise STTRateLimitError("deepgram") from exc
            raise STTProviderError("deepgram", str(exc)) from exc
        except Exception as exc:
            raise STTProviderError("deepgram", str(exc)) from exc

    def _transcribe_assemblyai(self, audio_path: str) -> dict[str, Any]:
        """Submit audio to AssemblyAI and poll until the transcript is ready.

        Uses the ``assemblyai`` SDK which handles upload + polling internally.

        Returns
        -------
        dict
            Raw assembled response dict.

        Raises
        ------
        STTProviderError
            If the transcript status is ``error`` or the SDK raises.
        """
        logger.info("Calling AssemblyAI (async upload + poll): file='%s'.", audio_path)
        try:
            aai.settings.api_key = self.api_keys["assemblyai"]
            cfg = aai.TranscriptionConfig(speaker_labels=True, speech_models=[aai.SpeechModel.universal])
            transcriber = aai.Transcriber(config=cfg)
            transcript = transcriber.transcribe(audio_path)

            if transcript.status == aai.TranscriptStatus.error:
                raise STTProviderError("assemblyai", transcript.error or "Unknown error")

            raw: dict[str, Any] = {
                "text": transcript.text or "",
                "utterances": [
                    {
                        "speaker": u.speaker,
                        "start": u.start,
                        "end": u.end,
                        "text": u.text,
                    }
                    for u in (transcript.utterances or [])
                ],
                "language_code": getattr(transcript, "language_code", "en"),
                "audio_duration": getattr(transcript, "audio_duration", 0.0),
                "_provider": "assemblyai",
            }
            logger.debug(
                "AssemblyAI raw response: %d utterance(s).", len(raw["utterances"])
            )
            return raw

        except (STTProviderError, STTTimeoutError, STTRateLimitError):
            raise
        except Exception as exc:
            raise STTProviderError("assemblyai", str(exc)) from exc

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------

    def _normalise(self, raw: dict[str, Any]) -> TranscriptResult:
        """Map a provider-specific raw dict to the unified ``TranscriptResult`` schema.

        Parameters
        ----------
        raw : dict
            Raw response from one of the ``_transcribe_*`` methods.

        Returns
        -------
        TranscriptResult
            Normalised dict with guaranteed keys: ``full_text``, ``segments``,
            ``language``, ``duration_seconds``, ``provider``,
            ``diarisation_available``.

        Raises
        ------
        NormalisationError
            If required keys are absent or the data cannot be coerced.
        """
        provider = raw.get("_provider", self.provider)

        try:
            if provider == "whisper":
                return self._normalise_whisper(raw)
            if provider == "deepgram":
                return self._normalise_deepgram(raw)
            if provider == "assemblyai":
                return self._normalise_assemblyai(raw)
            raise NormalisationError(provider, f"Unknown provider key: {provider}")
        except (NormalisationError, KeyError, TypeError, AttributeError) as exc:
            if isinstance(exc, NormalisationError):
                raise
            raise NormalisationError(provider, str(exc)) from exc

    def _normalise_whisper(self, raw: dict[str, Any]) -> TranscriptResult:
        """Normalise an OpenAI Whisper verbose_json response."""
        segments = []
        for seg in raw.get("segments", []):
            segments.append(
                {
                    "speaker": None,  # Whisper has no diarization
                    "start_time": float(seg.get("start", 0.0)),
                    "end_time": float(seg.get("end", 0.0)),
                    "text": seg.get("text", "").strip(),
                }
            )
        return {
            "full_text": raw["text"],
            "segments": segments,
            "language": raw.get("language", "en"),
            "duration_seconds": float(raw.get("duration", 0.0)),
            "provider": "whisper",
            "diarisation_available": False,
        }

    def _normalise_deepgram(self, raw: dict[str, Any]) -> TranscriptResult:
        """Normalise a Deepgram Nova diarization response."""
        try:
            result = raw["results"]["channels"][0]["alternatives"][0]
        except (KeyError, IndexError) as exc:
            raise NormalisationError("deepgram", f"Unexpected structure: {exc}") from exc

        full_text: str = result.get("transcript", "")
        words = result.get("words", [])

        # Build speaker-labelled segments by grouping consecutive words per speaker
        segments: list[dict] = []
        if words:
            current_speaker = words[0].get("speaker", 0)
            chunk_start = float(words[0].get("start", 0.0))
            chunk_words: list[str] = [words[0].get("punctuated_word", words[0].get("word", ""))]
            chunk_end = float(words[0].get("end", 0.0))

            for word in words[1:]:
                spk = word.get("speaker", current_speaker)
                if spk != current_speaker:
                    segments.append(
                        {
                            "speaker": f"Speaker {current_speaker}",
                            "start_time": chunk_start,
                            "end_time": chunk_end,
                            "text": " ".join(chunk_words),
                        }
                    )
                    current_speaker = spk
                    chunk_start = float(word.get("start", chunk_end))
                    chunk_words = []
                chunk_words.append(word.get("punctuated_word", word.get("word", "")))
                chunk_end = float(word.get("end", chunk_end))

            segments.append(
                {
                    "speaker": f"Speaker {current_speaker}",
                    "start_time": chunk_start,
                    "end_time": chunk_end,
                    "text": " ".join(chunk_words),
                }
            )

        # Duration from metadata
        duration = 0.0
        try:
            duration = float(
                raw["metadata"]["duration"]
            )
        except (KeyError, TypeError, ValueError):
            pass

        return {
            "full_text": full_text,
            "segments": segments,
            "language": raw.get("metadata", {}).get("language", "en"),
            "duration_seconds": duration,
            "provider": "deepgram",
            "diarisation_available": True,
        }

    def _normalise_assemblyai(self, raw: dict[str, Any]) -> TranscriptResult:
        """Normalise an AssemblyAI utterances response."""
        segments = [
            {
                "speaker": f"Speaker {u['speaker']}",
                "start_time": round(u["start"] / 1000, 3),  # ms → s
                "end_time": round(u["end"] / 1000, 3),
                "text": u["text"],
            }
            for u in raw.get("utterances", [])
        ]
        return {
            "full_text": raw.get("text", ""),
            "segments": segments,
            "language": raw.get("language_code", "en"),
            "duration_seconds": float(raw.get("audio_duration", 0.0)),
            "provider": "assemblyai",
            "diarisation_available": True,
        }
