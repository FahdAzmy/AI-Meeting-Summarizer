"""Provider-specific response normalisation for transcription."""

from __future__ import annotations

from typing import Any, Callable

from modules.stt_errors import NormalisationError
from modules._transcription.types import TranscriptResult, TranscriptSegment


def normalise(
    raw: dict[str, Any],
    *,
    current_provider: str,
    normalisers: dict[str, Callable[[dict[str, Any]], TranscriptResult]],
) -> TranscriptResult:
    """Map a provider-specific raw dict to the unified TranscriptResult schema."""
    provider = raw.get("_provider", current_provider)

    try:
        normaliser = normalisers.get(provider)
        if normaliser is not None:
            return normaliser(raw)
        raise NormalisationError(provider, f"Unknown provider key: {provider}")
    except (NormalisationError, KeyError, TypeError, AttributeError) as exc:
        if isinstance(exc, NormalisationError):
            raise
        raise NormalisationError(provider, str(exc)) from exc


def normalise_whisper(raw: dict[str, Any]) -> TranscriptResult:
    """Normalise an OpenAI Whisper verbose_json response."""
    segments: list[TranscriptSegment] = []
    for seg in raw.get("segments", []):
        segments.append(
            {
                "speaker": None,
                "start_time": float(segment_value(seg, "start", 0.0)),
                "end_time": float(segment_value(seg, "end", 0.0)),
                "text": str(segment_value(seg, "text", "")).strip(),
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


def segment_value(segment: Any, key: str, default: Any) -> Any:
    """Read a segment value from dict-like or SDK object responses."""
    if isinstance(segment, dict):
        return segment.get(key, default)
    return getattr(segment, key, default)


def normalise_deepgram(raw: dict[str, Any]) -> TranscriptResult:
    """Normalise a Deepgram Nova diarization response."""
    try:
        result = raw["results"]["channels"][0]["alternatives"][0]
    except (KeyError, IndexError) as exc:
        raise NormalisationError("deepgram", f"Unexpected structure: {exc}") from exc

    full_text: str = result.get("transcript", "")
    words = result.get("words", [])
    segments = group_words_by_speaker(words)

    duration = 0.0
    try:
        duration = float(raw["metadata"]["duration"])
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


def group_words_by_speaker(words: list[dict[str, Any]]) -> list[TranscriptSegment]:
    """Group consecutive Deepgram words into speaker-labelled segments."""
    if not words:
        return []

    segments: list[TranscriptSegment] = []
    current_speaker = words[0].get("speaker", 0)
    chunk_start = float(words[0].get("start", 0.0))
    chunk_end = float(words[0].get("end", 0.0))
    chunk_words: list[str] = [
        words[0].get("punctuated_word", words[0].get("word", ""))
    ]

    for word in words[1:]:
        speaker = word.get("speaker", current_speaker)
        if speaker != current_speaker:
            segments.append(
                {
                    "speaker": f"Speaker {current_speaker}",
                    "start_time": chunk_start,
                    "end_time": chunk_end,
                    "text": " ".join(chunk_words),
                }
            )
            current_speaker = speaker
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
    return segments


def normalise_assemblyai(raw: dict[str, Any]) -> TranscriptResult:
    """Normalise an AssemblyAI utterances response."""
    segments = [
        {
            "speaker": f"Speaker {u['speaker']}",
            "start_time": round(u["start"] / 1000, 3),
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
