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


def merge_speaker_names(
    speaker_stats: dict[str, Any] | None,
    text_speaker_analysis: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Replace generic 'Speaker N' labels with real names via rank-based matching.

    Both analytics layers produce speaker lists sorted by speaking time
    (descending).  The speaker who talked the most in Layer 1 (STT) is
    assumed to be the same person who talked the most in Layer 2 (LLM
    text detection).  A ``name_mapping`` dict is attached to the result
    so downstream verification (Solution 4) can reference the original
    generic labels.
    """
    if not speaker_stats or not text_speaker_analysis:
        return speaker_stats

    stt_speakers = speaker_stats.get("speakers", [])
    llm_speakers = text_speaker_analysis.get("speakers", [])

    if not stt_speakers or not llm_speakers:
        return speaker_stats

    # Build mapping: generic label → real name (by rank order)
    name_map: dict[str, str] = {}
    for i, stt_spk in enumerate(stt_speakers):
        if i < len(llm_speakers):
            llm_name = llm_speakers[i]["speaker"]
            stt_label = stt_spk["speaker"]
            # Only replace if the LLM actually found a real name
            if not llm_name.lower().startswith("speaker "):
                name_map[stt_label] = llm_name

    if not name_map:
        return speaker_stats

    # Apply mapping to speaker list
    merged_speakers = []
    for spk in stt_speakers:
        new_spk = dict(spk)
        if spk["speaker"] in name_map:
            new_spk["speaker"] = name_map[spk["speaker"]]
        merged_speakers.append(new_spk)

    merged: dict[str, Any] = dict(speaker_stats)
    merged["speakers"] = merged_speakers

    # Update most_active_speaker label
    old_most_active = speaker_stats.get("most_active_speaker", "")
    if old_most_active in name_map:
        merged["most_active_speaker"] = name_map[old_most_active]

    merged["name_mapping"] = name_map
    merged["detection_method"] = "stt_diarisation+llm_name_merge"
    return merged
