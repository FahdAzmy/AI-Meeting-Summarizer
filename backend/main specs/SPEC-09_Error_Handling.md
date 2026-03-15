# SPEC-09: Error Handling & Logging

| Field            | Details                                  |
|------------------|------------------------------------------|
| **Traceability** | FR12, NFR4, NFR11, NFR12                 |
| **Version**      | 1.0                                      |
| **Date**         | March 12, 2026                           |

---

## 09.1 Error Handling Matrix

| Module              | Error                 | Severity | Fallback                                                |
|---------------------|-----------------------|----------|---------------------------------------------------------|
| Meeting Access      | `MeetingJoinError`    | Critical | Retry 3× → failure email to participants → dashboard notification → abort. |
| Meeting Access      | `PlatformNotSupported`| Critical | Abort immediately → log unsupported URL.                |
| Audio Capture       | `OBSConnectionError`  | Critical | Log → prompt user to check OBS → abort.                 |
| Audio Capture       | `EmptyRecordingError` | High     | Log → abort pipeline (nothing to transcribe).           |
| Transcription       | `STTRateLimitError`   | Medium   | Switch to fallback STT provider → retry once.           |
| Transcription       | `STTTimeoutError`     | Medium   | Exponential backoff retry (3 attempts max).             |
| Summarisation       | `LLMAPIError`         | Medium   | Retry 2× → fallback to basic extractive summary.        |
| Summarisation       | `EmptyTranscriptError`| High     | Skip summary → store transcript only → set `"failed"`.  |
| Output & Storage    | `EmailDeliveryError`  | Low      | Log failed recipients → continue with storage.          |
| Output & Storage    | `SheetsWriteError`    | Medium   | Fallback to local CSV → log warning.                    |
| Output & Storage    | `DatabaseWriteError`  | High     | Log → set status `"failed"` (Beanie/MongoDB save error).  |

---

## 09.2 Logging Specification

**Logger:** Python `logging` module via `utils/logger.py`.

| Level    | Usage                                                     |
|----------|-----------------------------------------------------------|
| DEBUG    | API payloads, timing data, internal state.                |
| INFO     | Step start/complete, key milestones.                      |
| WARNING  | Retries, fallback activations, non-critical issues.       |
| ERROR    | Step failures that halt processing.                       |
| CRITICAL | Pipeline-level failures that require intervention.        |

**Format:**
```
[{timestamp}] [{level}] [{module}] {message}
```

**Example:**
```
[2026-03-12 14:30:15] [INFO] [meeting_access] Joining meeting: https://meet.google.com/abc-defg
[2026-03-12 14:30:22] [INFO] [meeting_access] Successfully joined (Google Meet)
[2026-03-12 15:01:10] [WARNING] [transcription] Whisper API rate limited — switching to Deepgram
```

---

## 09.3 Session Log File

Each meeting session produces a JSON log at `./logs/session_{session_id}.json`:

```json
{
    "session_id": "20260312_143015",
    "meeting_link": "https://meet.google.com/abc-defg-hij",
    "platform": "google_meet",
    "join_time": "2026-03-12T14:30:22",
    "leave_time": "2026-03-12T15:01:03",
    "recording_duration_sec": 1841,
    "audio_file": "./recordings/20260312_143015.wav",
    "stt_provider": "whisper",
    "transcription_time_sec": 202,
    "summary_generated": true,
    "emails_sent": ["alice@example.com", "bob@example.com"],
    "emails_failed": [],
    "storage_backend": "database",
    "storage_status": "success",
    "errors": []
}
```

---

## 09.4 Acceptance Criteria

| #  | Criteria                                                             | Verified |
|----|----------------------------------------------------------------------|----------|
| 1  | Session log JSON file produced for each meeting.                     | ☐        |
| 2  | Errors logged with correct severity levels.                          | ☐        |
