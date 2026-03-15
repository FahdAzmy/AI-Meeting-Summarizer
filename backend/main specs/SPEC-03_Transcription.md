# SPEC-03: Transcription Module

| Field            | Details                                  |
|------------------|------------------------------------------|
| **File**         | `modules/transcription.py`               |
| **Class**        | `Transcription`                          |
| **Traceability** | FR5, FR6, NFR2, NFR10                    |
| **Version**      | 1.0                                      |
| **Date**         | March 12, 2026                           |

---

## 03.1 Class Interface

```python
class Transcription:
    def __init__(self, provider: str = "whisper") -> None
    def transcribe(self, audio_path: str) -> dict       # → TranscriptResult
    def _transcribe_whisper(self, audio_path: str) -> dict
    def _transcribe_deepgram(self, audio_path: str) -> dict
    def _transcribe_assemblyai(self, audio_path: str) -> dict
    def _normalise(self, raw: dict, provider: str) -> dict
```

---

## 03.2 Provider Routing

```python
def transcribe(self, audio_path: str) -> dict:
    provider_map = {
        "whisper": self._transcribe_whisper,
        "deepgram": self._transcribe_deepgram,
        "assemblyai": self._transcribe_assemblyai,
    }
    fn = provider_map.get(self.provider)
    if not fn:
        raise ValueError(f"Unknown STT provider: {self.provider}")
    raw = fn(audio_path)
    return self._normalise(raw, self.provider)
```

---

## 03.3 Unified Output Schema — `TranscriptResult`

Every provider's response is normalised to this format:

```python
TranscriptResult = {
    "full_text": str,                    # Complete transcription
    "segments": [                        # list[Segment]
        {
            "speaker": str | None,       # "Speaker 1" — None if no diarisation
            "start_time": float,         # seconds from start
            "end_time": float,           # seconds from start
            "text": str                  # segment text
        }
    ],
    "language": str,                     # ISO 639-1 (e.g., "en")
    "duration_seconds": float,           # total audio duration
    "provider": str,                     # "whisper" | "deepgram" | "assemblyai"
    "diarisation_available": bool        # True if speaker labels present
}
```

---

## 03.4 Provider Specifications

### Whisper API **[M]**

| Property     | Value                                                 |
|--------------|-------------------------------------------------------|
| Endpoint     | `https://api.openai.com/v1/audio/transcriptions`      |
| Auth         | `Authorization: Bearer {WHISPER_API_KEY}`             |
| Model        | `whisper-1`                                           |
| Input format | File upload (multipart) — `.wav`, `.mp3`, `.m4a`      |
| Max file     | 25 MB (chunk if larger)                               |
| Diarisation  | Not natively supported                                |

### Deepgram **[S]**

| Property     | Value                                                 |
|--------------|-------------------------------------------------------|
| Endpoint     | `https://api.deepgram.com/v1/listen`                  |
| Auth         | `Authorization: Token {DEEPGRAM_API_KEY}`             |
| Features     | `?diarize=true&punctuate=true&utterances=true`        |
| Diarisation  | ✅ Supported via `diarize=true`                       |

### AssemblyAI **[S]**

| Property     | Value                                                 |
|--------------|-------------------------------------------------------|
| Endpoint     | `https://api.assemblyai.com/v2/transcript`            |
| Auth         | `Authorization: {ASSEMBLYAI_API_KEY}`                 |
| Features     | `speaker_labels: true`                                |
| Diarisation  | ✅ Supported via `speaker_labels`                     |
| Workflow     | Upload → poll for completion → fetch result           |

---

## 03.5 Retry Policy

| Scenario          | Strategy                                              |
|-------------------|-------------------------------------------------------|
| Timeout (408)     | Exponential backoff: 5s → 10s → 20s (3 attempts max) |
| Rate limit (429)  | Switch to fallback provider → retry once              |
| Server error (5xx)| Retry 3 times with 10s delay                          |
| Auth error (401)  | Abort immediately — log API key issue                 |

---

## 03.6 Error Codes

| Code    | Name                    | Trigger                                        |
|---------|-------------------------|------------------------------------------------|
| TR-001  | `STTProviderError`      | API returned a non-200 response.               |
| TR-002  | `STTTimeoutError`       | API did not respond within timeout.            |
| TR-003  | `STTRateLimitError`     | API returned 429 — rate limited.               |
| TR-004  | `AudioTooLargeError`    | File exceeds provider's max size limit.        |
| TR-005  | `NormalisationError`    | Could not parse provider's response format.    |

---

## 03.7 Acceptance Criteria

| #  | Criteria                                                             | Verified |
|----|----------------------------------------------------------------------|----------|
| 1  | Whisper API transcribes audio and returns normalised output.         | ☐        |
| 2  | Deepgram transcribes audio with diarisation.                         | ☐        |
| 3  | AssemblyAI transcribes audio with speaker labels.                    | ☐        |
| 4  | Provider switching works when primary provider fails.                | ☐        |
