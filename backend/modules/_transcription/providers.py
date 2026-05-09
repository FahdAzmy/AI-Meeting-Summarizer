"""Provider calls for the transcription router."""

from __future__ import annotations

import logging
import mimetypes
from typing import Any

from modules.stt_errors import (
    STTProviderError,
    STTRateLimitError,
    STTTimeoutError,
)
from modules._transcription.constants import DEEPGRAM_LISTEN_URL

logger = logging.getLogger(__name__)


def transcribe_whisper(
    *,
    audio_path: str,
    language_code: str | None,
    get_client: Any,
    openai_module: Any,
) -> dict[str, Any]:
    """Upload audio to OpenAI Whisper-1 and return the raw response dict."""
    logger.info("Calling OpenAI Whisper: file='%s'.", audio_path)
    try:
        client = get_client()
        with open(audio_path, "rb") as audio_file:
            kwargs: dict[str, Any] = {
                "model": "whisper-1",
                "file": audio_file,
                "response_format": "verbose_json",
                "timestamp_granularities": ["segment"],
            }
            if language_code:
                kwargs["language"] = language_code

            response = client.audio.transcriptions.create(**kwargs)

        raw: dict[str, Any] = {
            "text": response.text,
            "segments": response.segments or [],
            "language": getattr(response, "language", "en"),
            "duration": getattr(response, "duration", 0.0),
            "_provider": "whisper",
        }
        logger.debug(
            "Whisper raw response received: %d segment(s).",
            len(raw["segments"]),
        )
        return raw

    except openai_module.APIStatusError as exc:
        status = exc.status_code
        if status == 408:
            raise STTTimeoutError("whisper", 1) from exc
        if status == 429:
            raise STTRateLimitError("whisper") from exc
        raise STTProviderError("whisper", str(exc)) from exc
    except Exception as exc:
        raise STTProviderError("whisper", str(exc)) from exc


def transcribe_deepgram(
    *,
    audio_path: str,
    language_code: str | None,
    api_key: str,
    requests_module: Any,
) -> dict[str, Any]:
    """Upload audio to Deepgram Nova with speaker diarization enabled."""
    url = DEEPGRAM_LISTEN_URL
    if language_code:
        url += f"&language={language_code}"
    else:
        url += "&detect_language=true"

    mime_type, _ = mimetypes.guess_type(audio_path)
    content_type = mime_type if mime_type else "audio/wav"

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": content_type,
    }
    logger.info(
        "Calling Deepgram: file='%s' (Content-Type: %s)",
        audio_path,
        content_type,
    )
    try:
        with open(audio_path, "rb") as f:
            payload = f.read()

        resp = requests_module.post(
            url,
            headers=headers,
            data=payload,
            timeout=600,
        )
        resp.raise_for_status()
        raw = resp.json()
        raw["_provider"] = "deepgram"
        return raw

    except requests_module.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 0
        if status == 408:
            raise STTTimeoutError("deepgram", 1) from exc
        if status == 429:
            raise STTRateLimitError("deepgram") from exc
        raise STTProviderError("deepgram", str(exc)) from exc
    except Exception as exc:
        raise STTProviderError("deepgram", str(exc)) from exc


def transcribe_assemblyai(
    *,
    audio_path: str,
    language_code: str | None,
    api_key: str,
    aai_module: Any,
) -> dict[str, Any]:
    """Submit audio to AssemblyAI and poll until the transcript is ready."""
    logger.info("Calling AssemblyAI (async upload + poll): file='%s'.", audio_path)
    try:
        aai_module.settings.api_key = api_key

        if language_code:
            logger.info("[ST] Forcing language_code='%s' for AssemblyAI.", language_code)
            cfg = aai_module.TranscriptionConfig(
                speaker_labels=True,
                speech_models=[aai_module.SpeechModel.universal],
                language_code=language_code,
            )
        else:
            logger.info(
                "[ST] language_code not set \u2013 using universal-2 with language detection."
            )
            cfg = aai_module.TranscriptionConfig(
                speaker_labels=True,
                speech_models=["universal-2"],
                language_detection=True,
            )

        transcriber = aai_module.Transcriber(config=cfg)
        transcript = transcriber.transcribe(audio_path)

        if transcript.status == aai_module.TranscriptStatus.error:
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
            "AssemblyAI raw response: %d utterance(s).",
            len(raw["utterances"]),
        )
        return raw

    except (STTProviderError, STTTimeoutError, STTRateLimitError):
        raise
    except Exception as exc:
        raise STTProviderError("assemblyai", str(exc)) from exc
