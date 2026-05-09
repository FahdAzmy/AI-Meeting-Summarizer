"""Speaker participation analytics for summarisation output."""

from __future__ import annotations

from typing import Any


def analyse_participation(
    segments: list[dict[str, Any]],
    *,
    detection_method: str | None = None,
) -> dict | None:
    """Compute per-speaker speaking time from diarised segments."""
    if not segments:
        return None

    diarised = [s for s in segments if s.get("speaker")]
    if not diarised:
        return None

    speaker_time: dict[str, float] = {}
    speaker_turns: dict[str, int] = {}

    for seg in diarised:
        speaker = seg["speaker"]
        start = float(seg.get("start_time", seg.get("start", 0)))
        end = float(seg.get("end_time", seg.get("end", 0)))
        duration = end - start
        speaker_time[speaker] = speaker_time.get(speaker, 0.0) + max(duration, 0.0)
        speaker_turns[speaker] = speaker_turns.get(speaker, 0) + 1

    total_duration = sum(speaker_time.values())
    if total_duration == 0:
        return None

    speakers_list = [
        {
            "speaker": spk,
            "total_speaking_time_sec": round(speaker_time[spk], 3),
            "percentage_of_meeting": round(
                (speaker_time[spk] / total_duration) * 100,
                2,
            ),
            "number_of_turns": speaker_turns[spk],
        }
        for spk in sorted(speaker_time, key=lambda s: speaker_time[s], reverse=True)
    ]

    most_active = speakers_list[0]["speaker"]
    result: dict[str, Any] = {
        "speakers": speakers_list,
        "most_active_speaker": most_active,
        "total_meeting_duration_sec": round(total_duration, 3),
    }
    if detection_method is not None:
        result["detection_method"] = detection_method
    return result
