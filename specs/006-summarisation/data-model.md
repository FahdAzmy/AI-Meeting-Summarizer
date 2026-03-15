# Data Model: Summarisation Module

This file defines the primary objects, attributes, and custom error enums utilized within the `summarisation.py` module context.

## 1. Summarisation (Class Router)

The controller orchestrating the LLM and the analytics mathematics.

- **model** (`str`) - State tracker representing the target text engine (`gpt-4-turbo`, `gpt-3.5`).
- **temperature** (`float`) - Locked execution strictness parameter (defaults to `0.3`).

## 2. MeetingReport (Unified Application Schema)

The specific Python `dict` exported by the module. This is precisely what the Frontend parses later in React.

```python
MeetingReport = {
    "summary": str,                     # Markdown formatted overview & points
    "action_items": [                   # List[dict]
        {
            "assignee": str,            
            "task": str,                
            "deadline": str | None      
        }
    ],
    "decisions": [str],                 # Purely isolated strategic calls
    "follow_up": [str],                 # Missing points identified
    "speaker_stats": {                  # None explicitly if diarization == False
        "speakers": [
            {
                "speaker": str,         # E.g. "Speaker 1"
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

## 3. Exceptions (Custom Error Structs)

To standardize pipeline abortion and the resulting error-payload outputs. Inherits from Pythons base `Exception`.

- `LLMAPIError` (`SM-001`): Tripped for explicit general `HTTP 500` API faults when querying the model framework.
- `LLMTimeoutError` (`SM-002`): Tripped when generation exceeds boundary limits or stalls natively. 
- `ParseError` (`SM-003`): Fired if JSON Mode parsing drops or fails to match the strict schema mapped back from the LLM endpoint natively.
- `EmptyTranscriptError` (`SM-004`): Fired actively passing 0 bytes natively bypassing logic.
