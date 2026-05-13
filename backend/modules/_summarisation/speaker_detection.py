"""Best-effort LLM-based speaker detection fallback."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from modules._summarisation.prompts import (
    SPEAKER_DETECTION_SYSTEM_PROMPT,
    build_speaker_detection_prompt,
)
from modules._summarisation.schemas import SpeakerDetectionSchema

logger = logging.getLogger(__name__)


def detect_speakers_from_text(
    transcript: dict[str, Any],
    *,
    call_llm: Callable[..., str],
    participant_hints: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Split transcript text into synthetic speaker-labelled segments.

    Parameters
    ----------
    participant_hints:
        Optional list of known participant names (e.g. extracted from email
        addresses — Solution 3).  When provided, the LLM prompt is enhanced
        with these names so the model prioritises confirmed identities.
    """
    full_text = transcript.get("full_text", "")
    if not full_text.strip():
        return transcript.get("segments", [])

    total_duration = float(transcript.get("duration_seconds", 0.0))
    user_prompt = f"Full meeting transcript:\n\n{full_text}"

    # Build prompt — with participant hints if available (Solution 3)
    system_prompt = build_speaker_detection_prompt(participant_hints)

    logger.info(
        "[SM] Text speaker detection: sending full transcript to LLM (%d chars, %d hints).",
        len(full_text),
        len(participant_hints) if participant_hints else 0,
    )

    try:
        raw_content = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            purpose="Text speaker detection",
        )
        payload = json.loads(raw_content)
        detection = SpeakerDetectionSchema(**payload)

        logger.info(
            "[SM] Text speaker detection complete: %d speakers, %d turns.",
            detection.speakers_identified,
            len(detection.turns),
        )

        if not detection.turns:
            return transcript.get("segments", [])

        total_words = sum(len(t.text.split()) for t in detection.turns)
        if total_words == 0:
            total_words = 1

        enriched_segments: list[dict[str, Any]] = []
        current_time = 0.0

        for turn in detection.turns:
            word_count = len(turn.text.split())
            turn_duration = (
                (word_count / total_words) * total_duration
                if total_duration > 0
                else 1.0
            )
            enriched_segments.append(
                {
                    "speaker": turn.speaker,
                    "start_time": round(current_time, 3),
                    "end_time": round(current_time + turn_duration, 3),
                    "text": turn.text,
                }
            )
            current_time += turn_duration

        return enriched_segments

    except Exception as exc:
        logger.warning(
            "[SM] Text speaker detection failed (non-fatal): %s",
            exc,
        )
        return transcript.get("segments", [])
