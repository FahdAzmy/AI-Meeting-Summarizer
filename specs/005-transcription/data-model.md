# Data Model: Transcription Module

This file defines the primary objects, attributes, and custom error enums utilized within the `transcription.py` module context.

## 1. Transcription (Class Router)

The controller orchestrating external API access.

- **provider** (`str`) - State tracker representing the currently targeted STT engine (`"whisper"`, `"deepgram"`, `"assemblyai"`).
- **api_keys** (`dict`) - Configuration structure housing the distinct bearer tokens.

## 2. TranscriptResult (Unified Application Schema)

The specific Python `dict` returned to the broader application. Regardless of provider, responses MUST conform geometrically to this struct.

```python
TranscriptResult = {
    "full_text": str,                    # The appended complete transcription string
    "segments": [                        # List[dict]
        {
            "speaker": str | None,       # "Speaker 1" — None if Diarization isn't supported (e.g. Whisper)
            "start_time": float,         # Timestamp (Seconds)
            "end_time": float,           # Timestamp (Seconds)
            "text": str                  # Exact literal string for this chunk
        }
    ],
    "language": str,                     # ISO 639-1 notation (e.g., "en")
    "duration_seconds": float,           # The total ingested audio metric
    "provider": str,                     # The provider successfully used
    "diarisation_available": bool        # Simple validation flag for downstream LLMs
}
```

## 3. Exceptions (Custom Error Structs)

To standardize pipeline abortion and the resulting error-payload outputs. Inherits from Pythons base `Exception`.

- `STTProviderError` (`TR-001`): Tripped for explicit general `HTTP 500` server failures or unknown `requests` exceptions.
- `STTTimeoutError` (`TR-002`): Tripped mapping `HTTP 408` drops. Drives the exponential backoff behaviors.
- `STTRateLimitError` (`TR-003`): Tripped mapping `HTTP 429` drops. Drives the fallback engine logic.
- `AudioTooLargeError` (`TR-004`): Tripped exclusively by `os.path.getsize` evaluating files above `25MB`.
- `NormalisationError` (`TR-005`): Tripped within `_normalise()` if the proprietary data from Deepgram/OpenAI lacks expected schema bounds.
