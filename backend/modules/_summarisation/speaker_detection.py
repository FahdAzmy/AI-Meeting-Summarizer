"""Best-effort LLM-based speaker detection fallback."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from modules._summarisation.prompts import SPEAKER_DETECTION_SYSTEM_PROMPT
from modules._summarisation.schemas import SpeakerDetectionSchema

logger = logging.getLogger(__name__)


def detect_speakers_from_text(
    transcript: dict[str, Any],
    *,
    call_llm: Callable[..., str],
) -> list[dict[str, Any]]:
    """Split transcript text into synthetic speaker-labelled segments."""
    full_text = transcript.get("full_text", "")
    if not full_text.strip():
        return transcript.get("segments", [])

    total_duration = float(transcript.get("duration_seconds", 0.0))
    user_prompt = f"Full meeting transcript:\n\n{full_text}"

    logger.info(
        "[SM] Text speaker detection: sending full transcript to LLM (%d chars).",
        len(full_text),
    )

    try:
        raw_content = call_llm(
            system_prompt=SPEAKER_DETECTION_SYSTEM_PROMPT,
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
