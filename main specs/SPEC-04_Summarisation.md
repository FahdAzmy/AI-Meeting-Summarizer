# SPEC-04: Summarisation & Analysis Module

| Field            | Details                                  |
|------------------|------------------------------------------|
| **File**         | `modules/summarisation.py`               |
| **Class**        | `Summarisation`                          |
| **Traceability** | FR7, FR10, NFR1                          |
| **Version**      | 1.0                                      |
| **Date**         | March 12, 2026                           |

---

## 04.1 Class Interface

```python
class Summarisation:
    def __init__(self) -> None
    def generate_report(self, transcript: dict) -> dict   # → MeetingReport
    def _generate_summary(self, text: str) -> str
    def _extract_action_items(self, text: str) -> list[dict]
    def _extract_decisions(self, text: str) -> list[str]
    def _analyse_participation(self, segments: list) -> dict | None
```

---

## 04.2 Output Schema — `MeetingReport`

```python
MeetingReport = {
    "summary": str,                     # Structured meeting summary (markdown)
    "action_items": [                   # list[ActionItem]
        {
            "assignee": str,            # Person assigned
            "task": str,                # Task description
            "deadline": str | None      # Deadline if mentioned
        }
    ],
    "decisions": [str],                 # List of decisions made
    "follow_up": [str],                 # Unresolved items needing attention
    "speaker_stats": {                  # None if diarisation unavailable
        "speakers": [
            {
                "speaker": str,
                "total_speaking_time_sec": float,
                "percentage_of_meeting": float,
                "number_of_turns": int
            }
        ],
        "most_active_speaker": str,
        "total_meeting_duration_sec": float
    } | None
}
```

---

## 04.3 LLM Prompt Specification

| Property         | Value                                                       |
|------------------|-------------------------------------------------------------|
| Model            | `Config.LLM_MODEL` (default: `gpt-4`)                      |
| Temperature      | `0.3` (low creativity → factual extraction)                 |
| Max tokens       | `2000`                                                      |
| System role      | "You are an AI meeting assistant that produces structured meeting summaries." |

**Prompt template:**

```
Analyse the following meeting transcript and produce a structured summary.

**Output Format (use exactly this structure):**
1. **Meeting Overview** — 2-3 sentence summary of purpose and outcome.
2. **Key Discussion Points** — Bullet list of main topics.
3. **Decisions Made** — Numbered list of decisions with context.
4. **Action Items** — JSON array: [{"assignee": "...", "task": "...", "deadline": "..."}]
5. **Follow-Up Required** — Bullet list of unresolved items.

**Transcript:**
{transcript_text}
```

---

## 04.4 Participation Analysis Logic

```python
def _analyse_participation(self, segments: list) -> dict | None:
    """Compute speaker statistics from diarised transcript segments."""
    if not segments or segments[0].get("speaker") is None:
        return None
    
    # For each speaker: sum duration, count turns
    # Calculate percentage = (speaker_time / total_time) * 100
    # Return structured speaker_stats dict
```

---

## 04.5 Performance Requirement

- A 30-minute meeting transcript must be summarised in **< 2 minutes** (NFR1 subset).
- Total pipeline post-processing (transcription + summarisation) must complete in **< 10 minutes** (NFR1).

---

## 04.6 Error Codes

| Code    | Name                    | Trigger                                        |
|---------|-------------------------|------------------------------------------------|
| SM-001  | `LLMAPIError`           | LLM API returned a non-200 response.           |
| SM-002  | `LLMTimeoutError`       | LLM API did not respond in time.               |
| SM-003  | `ParseError`            | Could not parse action items/decisions from LLM output. |
| SM-004  | `EmptyTranscriptError`  | Transcript text is empty — nothing to summarise.|

---

## 04.7 Acceptance Criteria

| #  | Criteria                                                             | Verified |
|----|----------------------------------------------------------------------|----------|
| 1  | LLM generates structured summary with all 5 sections.               | ☐        |
| 2  | Action items are extracted as structured JSON.                       | ☐        |
| 3  | Participation analysis produces speaker statistics.                  | ☐        |
| 4  | Summary generated within 2 minutes for 30-minute meeting.           | ☐        |
