# Technical Specifications Document
## AI-Powered Meeting Assistant

| Field             | Details                              |
|-------------------|--------------------------------------|
| **Project Title** | AI-Powered Meeting Assistant         |
| **Version**       | 1.0                                  |
| **Date**          | March 12, 2026                       |
| **Status**        | Draft                                |
| **References**    | PRD.md, Implementation_Plan.md       |

---

## Table of Contents

1. [SPEC-00: Frontend Dashboard](#spec-00-frontend-dashboard)
2. [SPEC-01: Meeting Access Module](#spec-01-meeting-access-module)
3. [SPEC-02: Audio Capture Module](#spec-02-audio-capture-module)
4. [SPEC-03: Transcription Module](#spec-03-transcription-module)
5. [SPEC-04: Summarisation & Analysis Module](#spec-04-summarisation--analysis-module)
6. [SPEC-05: Output & Storage Module](#spec-05-output--storage-module)
7. [SPEC-06: Pipeline Orchestrator](#spec-06-pipeline-orchestrator)
8. [SPEC-07: Configuration & Environment](#spec-07-configuration--environment)
9. [SPEC-08: Database Schema](#spec-08-database-schema)
10. [SPEC-09: Error Handling & Logging](#spec-09-error-handling--logging)
11. [SPEC-10: Test-Driven Development (TDD)](#spec-10-test-driven-development-tdd)

---

## Conventions

| Notation         | Meaning                                                  |
|------------------|----------------------------------------------------------|
| **[M]**          | Mandatory — must be implemented for MVP.                 |
| **[S]**          | Should — strongly recommended; defer only if blocked.    |
| **[C]**          | Could — nice-to-have; implement if time permits.         |
| `→`              | Returns / produces.                                      |
| `param: Type`    | Parameter with its expected type.                        |

---

## SPEC-00: Frontend Dashboard

**File:** `app.py` + `frontend/`
**Framework:** Flask 3.x (Jinja2 templates)
**Traceability:** FR-D1 through FR-D11, NFR3, NFR13, NFR14

### 00.1 Pages

| Page               | Template                 | Description                                               |
|--------------------|--------------------------|-----------------------------------------------------------|
| Dashboard          | `dashboard.html`         | Meeting link input, email list, "Join Meeting" button.    |
| Meetings History   | `history.html`           | Sortable table of past meetings with status badges.       |
| Meeting Detail     | `meeting_detail.html`    | Full summary, transcript, action items, speaker stats.    |
| Settings           | `settings.html`          | Storage toggle (DB/Sheets), STT provider, email config.   |

### 00.2 Route Specifications

#### `GET /` — Dashboard Page **[M]**

| Field        | Value                                                           |
|--------------|-----------------------------------------------------------------|
| Template     | `dashboard.html`                                                |
| Auth         | None (single-user system)                                       |
| Response     | 200 OK — renders the meeting input form                         |
| UI Elements  | `<input name="meeting_link">`, `<textarea name="emails">`, `<button>Join Meeting</button>` |

**Client-side behaviour:**
- `app.js` detects the meeting platform from the URL (regex match for `meet.google.com`, `zoom.us`, `teams.microsoft.com`) and renders a badge **[S]**.
- Form validates URL format and non-empty email list before submit **[S]**.

---

#### `POST /join` — Trigger Pipeline **[M]**

| Field        | Value                                                           |
|--------------|-----------------------------------------------------------------|
| Content-Type | `application/x-www-form-urlencoded`                             |
| Parameters   | `meeting_link: str` (required), `emails: str` (comma-separated, required) |
| Response     | 302 Redirect → `/`                                              |

**Processing Logic:**
1. Read `meeting_link` and `emails` from form body.
2. Query `Settings` table → retrieve `storage_backend` (default: `"database"`).
3. Spawn `threading.Thread(target=run_pipeline, args=(link, emails, backend))`.
4. Redirect to dashboard.

**Validation Rules:**

| Rule                        | Error Behaviour                                      |
|-----------------------------|------------------------------------------------------|
| `meeting_link` is empty     | Flash error → redirect to `/`                        |
| `meeting_link` is not a URL | Flash error → redirect to `/`                        |
| `emails` is empty           | Flash error → redirect to `/`                        |

---

#### `GET /status/<session_id>` — Pipeline Status **[S]**

| Field        | Value                                                           |
|--------------|-----------------------------------------------------------------|
| Response     | 200 OK — JSON object                                            |
| Content-Type | `application/json`                                              |

```json
{
    "session_id": "20260312_143015",
    "status": "transcribing",
    "step": 5,
    "total_steps": 7,
    "message": "Transcribing audio via Whisper API..."
}
```

---

#### `GET /history` — Meetings History **[M]**

| Field        | Value                                                           |
|--------------|-----------------------------------------------------------------|
| Template     | `history.html`                                                  |
| Query        | `Meeting.query.order_by(Meeting.date.desc()).all()`             |
| Context Var  | `meetings: list[Meeting]`                                       |

**Table columns rendered:** Date, Platform (badge), Duration, Summary preview (first 100 chars), Status (colour-coded), Action ("View Details" link).

**Performance:** Query must complete within 2 seconds for 100+ records (NFR13).

---

#### `GET /history/<int:meeting_id>` — Meeting Detail **[M]**

| Field        | Value                                                           |
|--------------|-----------------------------------------------------------------|
| Template     | `meeting_detail.html`                                           |
| Query        | `Meeting.query.get_or_404(meeting_id)`                          |
| Context Var  | `meeting: Meeting`                                              |
| 404          | Returned when `meeting_id` does not exist                       |

**Displayed sections:**
1. Meeting Overview (date, platform, duration, link)
2. Full Summary
3. Action Items table (parsed from JSON)
4. Decisions list (parsed from JSON)
5. Full Transcript (collapsible)
6. Speaker Statistics (if available)

---

#### `GET /settings` — Settings Page **[M]**

| Field        | Value                                                           |
|--------------|-----------------------------------------------------------------|
| Template     | `settings.html`                                                 |
| Query        | `Settings.query.first()` (creates default if None)              |
| Context Var  | `settings: Settings`                                            |

---

#### `POST /settings` — Save Settings **[M]**

| Field        | Value                                                           |
|--------------|-----------------------------------------------------------------|
| Parameters   | `storage_backend: str`, `stt_provider: str`, `email_sender: str`, `email_password: str` |
| Response     | 302 Redirect → `/settings`                                      |
| Side Effect  | Updates or creates `Settings` row in DB                         |

**Allowed values:**

| Parameter        | Valid Values                            |
|------------------|-----------------------------------------|
| `storage_backend`| `"database"`, `"google_sheets"`         |
| `stt_provider`   | `"whisper"`, `"deepgram"`, `"assemblyai"` |

Effect is **immediate** for all subsequent meetings (NFR14).

---

### 00.3 Static Assets

| File                    | Purpose                                              |
|-------------------------|------------------------------------------------------|
| `frontend/static/css/style.css` | Dashboard styling — responsive layout, badges, tables |
| `frontend/static/js/app.js`     | Platform detection, form validation, live status polling |

---

## SPEC-01: Meeting Access Module

**File:** `modules/meeting_access.py`
**Class:** `MeetingAccess`
**Traceability:** FR1, FR2, NFR5

### 01.1 Class Interface

```python
class MeetingAccess:
    detected_platform: str          # "google_meet" | "zoom" | "teams"
    
    def __init__(self) -> None
    def join(self, link: str) -> None
    def wait_until_end(self) -> None
    def leave(self) -> None
```

### 01.2 Method Specifications

#### `__init__()` **[M]**
- Initialises Chrome via `webdriver-manager` with the following flags:
  - `--disable-notifications`
  - `--use-fake-ui-for-media-stream`
  - `--use-fake-device-for-media-stream`
  - `--disable-blink-features=AutomationControlled`
- Stores the `WebDriver` instance as `self.driver`.

#### `join(link: str)` **[M]**
1. Call `_detect_platform(link)` → sets `self.detected_platform`.
2. Navigate to `link`.
3. Execute platform-specific join sequence:

| Platform       | Join Sequence                                                                  | Timeout |
|----------------|--------------------------------------------------------------------------------|---------|
| Google Meet    | Dismiss pre-join → mute mic → mute cam → click "Join now"                     | 60s     |
| Zoom (Web)     | Enter display name → click "Join" → handle waiting room                        | 90s     |
| MS Teams       | Click "Continue on this browser" → mute mic → mute cam → click "Join now"     | 90s     |

4. On timeout → raise `MeetingJoinError`.
5. On success → log join timestamp.

**Retry policy:** 3 attempts, 10-second delay between retries.

#### `wait_until_end()` **[M]**
- Poll the meeting page every 30 seconds.
- Detect meeting-ended signals:
  - Google Meet: "You've left the meeting" or "Meeting ended" header.
  - Zoom: browser URL changes or disconnect dialog.
  - Teams: "You left the meeting" banner.
- On detection → return control to the pipeline.

#### `leave()` **[M]**
- Click the platform's "Leave" button (if still in meeting).
- Call `self.driver.quit()` to close the browser instance.

### 01.3 Platform Detection

```python
def _detect_platform(link: str) -> str:
    """Returns 'google_meet' | 'zoom' | 'teams' | raises ValueError."""
    if "meet.google.com" in link:
        return "google_meet"
    elif "zoom.us" in link or "zoom.com" in link:
        return "zoom"
    elif "teams.microsoft.com" in link or "teams.live.com" in link:
        return "teams"
    else:
        raise ValueError(f"Unsupported meeting platform: {link}")
```

### 01.4 CSS Selectors (Configuration-Driven)

Selectors for each platform are stored in `config/selectors.json` for easy updates when platforms change their UI.

```json
{
    "google_meet": {
        "join_button": "button[jsname='Qx7uuf']",
        "mute_mic": "button[data-is-muted]",
        "end_screen": "div[data-call-ended]"
    },
    "zoom": {
        "join_button": "#joinBtn",
        "name_input": "#inputname",
        "waiting_room": ".waiting-room-container"
    },
    "teams": {
        "continue_browser": "a[data-tid='joinOnWeb']",
        "join_button": "button#prejoin-join-button",
        "end_banner": "div[data-tid='call-ended']"
    }
}
```

### 01.5 Error Codes

| Code    | Name                 | Trigger                                           |
|---------|----------------------|---------------------------------------------------|
| MA-001  | `MeetingJoinError`   | Failed to join after 3 retries.                   |
| MA-002  | `PlatformNotSupported` | Link does not match any supported platform.     |
| MA-003  | `BrowserInitError`   | Chrome/WebDriver failed to initialise.            |
| MA-004  | `WaitingRoomTimeout` | Host did not admit within 5 minutes.              |

---

## SPEC-02: Audio Capture Module

**File:** `modules/audio_capture.py`
**Class:** `AudioCapture`
**Traceability:** FR3, FR4, NFR6

### 02.1 Class Interface

```python
class AudioCapture:
    def __init__(self) -> None
    def start(self) -> None
    def stop(self) -> str          # → returns audio file path
    def healthcheck(self) -> bool
```

### 02.2 Method Specifications

#### `__init__()` **[M]**
- Connects to OBS via `obsws_python.ReqClient(host, port, password)` using values from `Config`.
- Raises `OBSConnectionError` if connection fails.

#### `start()` **[M]**
1. Call `healthcheck()` — abort if OBS is not ready.
2. Ensure output directory (`Config.RECORDINGS_DIR`) exists.
3. Execute `client.start_record()`.
4. Poll `client.get_record_status()` to confirm recording is active.
5. Log start timestamp.

#### `stop() → str` **[M]**
1. Execute `client.stop_record()`.
2. Retrieve output file path from OBS response.
3. Verify file exists and size > 0 bytes.
4. Return absolute file path as string.

#### `healthcheck() → bool` **[M]**
1. Attempt `client.get_version()` — verify OBS is responsive.
2. Check that a valid audio source is configured.
3. Return `True` if all checks pass, `False` otherwise.

### 02.3 Pre-flight Checks

| Check                          | Method                                  | Failure Action          |
|--------------------------------|-----------------------------------------|-------------------------|
| OBS process is running         | OBS WebSocket `get_version()`           | Raise `OBSNotRunning`   |
| WebSocket is reachable         | TCP connection to `host:port`           | Raise `OBSConnectionError` |
| Audio source is mapped         | `get_input_list()` contains audio source| Log warning             |
| Output directory is writable   | `os.access(dir, os.W_OK)`              | Create dir or raise     |

### 02.4 Output Format

| Property         | Value                                              |
|------------------|----------------------------------------------------|
| Default format   | `.wav` (lossless, best for STT accuracy)           |
| Alternative      | `.mp3` (smaller size, configurable via OBS)        |
| Sample rate      | 44100 Hz (OBS default)                             |
| Channels         | Stereo (system audio capture)                      |
| File naming      | `{session_id}.wav` (e.g., `20260312_143015.wav`)   |
| Storage path     | `./recordings/{filename}`                          |

### 02.5 Error Codes

| Code    | Name                   | Trigger                                         |
|---------|------------------------|-------------------------------------------------|
| AC-001  | `OBSConnectionError`   | Cannot connect to OBS WebSocket.                |
| AC-002  | `OBSNotRunning`        | OBS Studio is not running.                      |
| AC-003  | `RecordingStartError`  | OBS failed to start recording.                  |
| AC-004  | `RecordingStopError`   | OBS failed to stop recording.                   |
| AC-005  | `EmptyRecordingError`  | Output file is 0 bytes (no audio captured).     |

---

## SPEC-03: Transcription Module

**File:** `modules/transcription.py`
**Class:** `Transcription`
**Traceability:** FR5, FR6, NFR2, NFR10

### 03.1 Class Interface

```python
class Transcription:
    def __init__(self, provider: str = "whisper") -> None
    def transcribe(self, audio_path: str) -> dict       # → TranscriptResult
    def _transcribe_whisper(self, audio_path: str) -> dict
    def _transcribe_deepgram(self, audio_path: str) -> dict
    def _transcribe_assemblyai(self, audio_path: str) -> dict
    def _normalise(self, raw: dict, provider: str) -> dict
```

### 03.2 Provider Routing

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

### 03.3 Unified Output Schema — `TranscriptResult`

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

### 03.4 Provider Specifications

#### Whisper API **[M]**

| Property     | Value                                                 |
|--------------|-------------------------------------------------------|
| Endpoint     | `https://api.openai.com/v1/audio/transcriptions`      |
| Auth         | `Authorization: Bearer {WHISPER_API_KEY}`             |
| Model        | `whisper-1`                                           |
| Input format | File upload (multipart) — `.wav`, `.mp3`, `.m4a`      |
| Max file     | 25 MB (chunk if larger)                               |
| Diarisation  | Not natively supported                                |

#### Deepgram **[S]**

| Property     | Value                                                 |
|--------------|-------------------------------------------------------|
| Endpoint     | `https://api.deepgram.com/v1/listen`                  |
| Auth         | `Authorization: Token {DEEPGRAM_API_KEY}`             |
| Features     | `?diarize=true&punctuate=true&utterances=true`        |
| Diarisation  | ✅ Supported via `diarize=true`                       |

#### AssemblyAI **[S]**

| Property     | Value                                                 |
|--------------|-------------------------------------------------------|
| Endpoint     | `https://api.assemblyai.com/v2/transcript`            |
| Auth         | `Authorization: {ASSEMBLYAI_API_KEY}`                 |
| Features     | `speaker_labels: true`                                |
| Diarisation  | ✅ Supported via `speaker_labels`                     |
| Workflow     | Upload → poll for completion → fetch result           |

### 03.5 Retry Policy

| Scenario          | Strategy                                              |
|-------------------|-------------------------------------------------------|
| Timeout (408)     | Exponential backoff: 5s → 10s → 20s (3 attempts max) |
| Rate limit (429)  | Switch to fallback provider → retry once              |
| Server error (5xx)| Retry 3 times with 10s delay                          |
| Auth error (401)  | Abort immediately — log API key issue                 |

### 03.6 Error Codes

| Code    | Name                    | Trigger                                        |
|---------|-------------------------|------------------------------------------------|
| TR-001  | `STTProviderError`      | API returned a non-200 response.               |
| TR-002  | `STTTimeoutError`       | API did not respond within timeout.            |
| TR-003  | `STTRateLimitError`     | API returned 429 — rate limited.               |
| TR-004  | `AudioTooLargeError`    | File exceeds provider's max size limit.        |
| TR-005  | `NormalisationError`    | Could not parse provider's response format.    |

---

## SPEC-04: Summarisation & Analysis Module

**File:** `modules/summarisation.py`
**Class:** `Summarisation`
**Traceability:** FR7, FR10, NFR1

### 04.1 Class Interface

```python
class Summarisation:
    def __init__(self) -> None
    def generate_report(self, transcript: dict) -> dict   # → MeetingReport
    def _generate_summary(self, text: str) -> str
    def _extract_action_items(self, text: str) -> list[dict]
    def _extract_decisions(self, text: str) -> list[str]
    def _analyse_participation(self, segments: list) -> dict | None
```

### 04.2 Output Schema — `MeetingReport`

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

### 04.3 LLM Prompt Specification

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

### 04.4 Participation Analysis Logic

```python
def _analyse_participation(self, segments: list) -> dict | None:
    """Compute speaker statistics from diarised transcript segments."""
    if not segments or segments[0].get("speaker") is None:
        return None
    
    # For each speaker: sum duration, count turns
    # Calculate percentage = (speaker_time / total_time) * 100
    # Return structured speaker_stats dict
```

### 04.5 Performance Requirement

- A 30-minute meeting transcript must be summarised in **< 2 minutes** (NFR1 subset).
- Total pipeline post-processing (transcription + summarisation) must complete in **< 10 minutes** (NFR1).

### 04.6 Error Codes

| Code    | Name                    | Trigger                                        |
|---------|-------------------------|------------------------------------------------|
| SM-001  | `LLMAPIError`           | LLM API returned a non-200 response.           |
| SM-002  | `LLMTimeoutError`       | LLM API did not respond in time.               |
| SM-003  | `ParseError`            | Could not parse action items/decisions from LLM output. |
| SM-004  | `EmptyTranscriptError`  | Transcript text is empty — nothing to summarise.|

---

## SPEC-05: Output & Storage Module

**File:** `modules/output_storage.py`
**Class:** `OutputStorage`
**Traceability:** FR8, FR9, NFR7, NFR8

### 05.1 Class Interface

```python
class OutputStorage:
    def __init__(self, backend: str = "database") -> None
    def send_email(self, recipients: list[str], report: dict) -> dict
    def store(self, report: dict, transcript: dict) -> None
    def _store_to_database(self, report: dict, transcript: dict) -> None
    def _store_to_sheets(self, report: dict, transcript: dict) -> None
    def _format_email_body(self, report: dict) -> str
```

### 05.2 Storage Backend Router

```python
def store(self, report, transcript):
    if self.backend == "database":
        self._store_to_database(report, transcript)
    elif self.backend == "google_sheets":
        self._store_to_sheets(report, transcript)
    else:
        raise ValueError(f"Unknown storage backend: {self.backend}")
```

### 05.3 Email Specification

| Property         | Value                                                       |
|------------------|-------------------------------------------------------------|
| Protocol         | SMTP over SSL (port 465)                                    |
| SMTP Host        | `smtp.gmail.com` (configurable)                             |
| Sender           | `Config.EMAIL_SENDER` (or from Settings table)              |
| Content-Type     | `multipart/alternative` (HTML body)                         |
| Subject format   | `"Meeting Summary — {platform} — {date}"`                   |

**Email body structure (HTML):**
1. Meeting overview header
2. Key discussion points
3. Action items table
4. Decisions list
5. Link to full transcript (if accessible)

**Return schema:**

```python
{
    "sent": ["alice@example.com", "bob@example.com"],
    "failed": [],
    "total": 2
}
```

### 05.4 Database Storage Specification

When `backend == "database"`, write all fields to the `Meeting` model:

| Meeting Field     | Source                                    |
|-------------------|-------------------------------------------|
| `summary`         | `report["summary"]`                       |
| `action_items`    | `json.dumps(report["action_items"])`      |
| `decisions`       | `json.dumps(report["decisions"])`         |
| `transcript`      | `transcript["full_text"]`                 |
| `speaker_stats`   | `json.dumps(report.get("speaker_stats"))` |
| `duration_minutes`| `transcript["duration_seconds"] // 60`    |
| `status`          | `"completed"`                             |

### 05.5 Google Sheets Storage Specification

When `backend == "google_sheets"`, append a row using `gspread`:

| Column (A-I)     | Value                                     |
|-------------------|-------------------------------------------|
| A: Meeting Date   | `datetime.now().isoformat()`              |
| B: Meeting Link   | Original meeting URL                      |
| C: Duration       | Duration in minutes                       |
| D: Participants   | Comma-separated email list                |
| E: Summary        | Generated summary text                    |
| F: Action Items   | JSON string of action items               |
| G: Decisions      | JSON string of decisions                  |
| H: Transcript     | Full text (or "See local file" if too long)|
| I: Status         | `"Success"` or `"Failed"`                 |

**Authentication:** Google Sheets API via service account JSON (`credentials.json`).

### 05.6 Error Codes

| Code    | Name                     | Trigger                                       |
|---------|--------------------------|-----------------------------------------------|
| OS-001  | `EmailDeliveryError`     | SMTP connection failed or send error.         |
| OS-002  | `SheetsWriteError`       | Google Sheets API returned error.             |
| OS-003  | `DatabaseWriteError`     | SQLAlchemy commit failed.                     |
| OS-004  | `InvalidBackendError`    | Unknown `storage_backend` value.              |

**Fallback:** If Google Sheets write fails → fall back to local CSV file at `./summaries/{session_id}.csv`.

---

## SPEC-06: Pipeline Orchestrator

**File:** `main.py`
**Function:** `run_pipeline()`
**Traceability:** All FR, NFR1, NFR9

### 06.1 Function Signature

```python
def run_pipeline(
    meeting_link: str,
    participant_emails: list[str],
    storage_backend: str = "database"
) -> None
```

### 06.2 Pipeline Steps

| Step | Action                  | Module Used       | Status Value    | Error Handling                      |
|------|-------------------------|-------------------|-----------------|-------------------------------------|
| 1    | Join meeting            | `MeetingAccess`   | `"joining"`     | Retry 3× → abort                   |
| 2    | Start recording         | `AudioCapture`    | `"recording"`   | Log + abort                         |
| 3    | Wait for meeting end    | `MeetingAccess`   | `"recording"`   | Monitor connection                  |
| 4    | Stop recording          | `AudioCapture`    | `"recording"`   | Log partial                         |
| 5    | Transcribe audio        | `Transcription`   | `"transcribing"`| Retry / switch provider             |
| 6    | Generate summary        | `Summarisation`   | `"summarising"` | Retry → basic extraction fallback  |
| 7    | Send email + store data | `OutputStorage`   | `"delivering"`  | Log failed recipients               |
| ✓    | Complete                | —                 | `"completed"`   | —                                   |
| ✗    | Failure at any step     | —                 | `"failed"`      | Error logged; `Meeting.status` set  |

### 06.3 Meeting Record Tracking

A `Meeting` database record is created at Step 1 and progressively updated with data at each step. This enables the History page to show live status for in-progress meetings.

### 06.4 Thread Safety

- Each pipeline run executes in its own `threading.Thread`.
- Database operations require an **application context** (`app.app_context()`).
- No shared mutable state between threads.
- Sequential meeting processing (NFR9) — the user can submit multiple but they execute one at a time if system resources are limited.

---

## SPEC-07: Configuration & Environment

**File:** `config.py` + `.env`
**Class:** `Config`

### 07.1 Environment Variables

| Variable                       | Type   | Default              | Description                         |
|--------------------------------|--------|----------------------|-------------------------------------|
| `SECRET_KEY`                   | str    | `"dev-secret-key"`   | Flask session secret                |
| `DATABASE_URI`                 | str    | `"sqlite:///meetings.db"` | SQLAlchemy connection string   |
| `STORAGE_BACKEND`              | str    | `"database"`         | Default storage (overridden by UI)  |
| `STT_PROVIDER`                 | str    | `"whisper"`          | Default STT provider                |
| `WHISPER_API_KEY`              | str    | —                    | OpenAI API key                      |
| `DEEPGRAM_API_KEY`             | str    | —                    | Deepgram API key                    |
| `ASSEMBLYAI_API_KEY`           | str    | —                    | AssemblyAI API key                  |
| `OPENAI_API_KEY`               | str    | —                    | LLM API key                         |
| `LLM_MODEL`                    | str    | `"gpt-4"`            | LLM model name                      |
| `OBS_WEBSOCKET_HOST`           | str    | `"localhost"`        | OBS WebSocket host                  |
| `OBS_WEBSOCKET_PORT`           | int    | `4455`               | OBS WebSocket port                  |
| `OBS_WEBSOCKET_PASSWORD`       | str    | `""`                 | OBS WebSocket password              |
| `EMAIL_SENDER`                 | str    | —                    | Sender email address                |
| `EMAIL_PASSWORD`               | str    | —                    | Sender app password                 |
| `GOOGLE_SHEETS_CRED_FILE`      | str    | `"credentials.json"` | Sheets service account key file     |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | str    | —                    | Target spreadsheet ID               |
| `RECORDINGS_DIR`               | str    | `"./recordings"`     | Audio output directory              |
| `TRANSCRIPTS_DIR`              | str    | `"./transcripts"`    | Transcript output directory         |
| `SUMMARIES_DIR`                | str    | `"./summaries"`      | Summary output directory            |
| `LOGS_DIR`                     | str    | `"./logs"`           | Log file directory                  |

### 07.2 Settings Override Hierarchy

```
.env defaults  →  overridden by  →  Settings table (user-configured via dashboard)
```

When the user changes a setting in the Settings page, it takes precedence over `.env` defaults for `storage_backend`, `stt_provider`, `email_sender`, and `email_password`.

---

## SPEC-08: Database Schema

**File:** `models.py`
**ORM:** Flask-SQLAlchemy

### 08.1 Meeting Table

| Column            | Type             | Constraints                      | Description                     |
|-------------------|------------------|----------------------------------|---------------------------------|
| `id`              | `Integer`        | PK, auto-increment              | Unique meeting ID               |
| `session_id`      | `String(50)`     | Unique, Not Null                 | Timestamp-based session ID      |
| `meeting_link`    | `String(500)`    | Not Null                         | Original meeting URL            |
| `platform`        | `String(50)`     | Nullable                         | `google_meet` / `zoom` / `teams`|
| `date`            | `DateTime`       | Default: `utcnow()`             | Meeting date/time               |
| `duration_minutes`| `Integer`        | Nullable                         | Meeting duration in minutes     |
| `participants`    | `Text`           | Nullable                         | Comma-separated email list      |
| `transcript`      | `Text`           | Nullable                         | Full transcription text         |
| `summary`         | `Text`           | Nullable                         | Generated summary               |
| `action_items`    | `Text`           | Nullable                         | JSON string                     |
| `decisions`       | `Text`           | Nullable                         | JSON string                     |
| `speaker_stats`   | `Text`           | Nullable                         | JSON string                     |
| `status`          | `String(20)`     | Default: `"pending"`             | Pipeline status                 |
| `audio_file_path` | `String(500)`    | Nullable                         | Path to recorded audio          |
| `storage_backend` | `String(20)`     | Nullable                         | `database` / `google_sheets`    |

**Status lifecycle:** `pending` → `joining` → `recording` → `transcribing` → `summarising` → `delivering` → `completed` | `failed`

### 08.2 Settings Table

| Column            | Type             | Constraints                      | Description                     |
|-------------------|------------------|----------------------------------|---------------------------------|
| `id`              | `Integer`        | PK                               | Always 1 (singleton)            |
| `storage_backend` | `String(20)`     | Default: `"database"`           | Active storage backend          |
| `stt_provider`    | `String(20)`     | Default: `"whisper"`            | Active STT provider             |
| `email_sender`    | `String(200)`    | Nullable                         | Sender email address            |
| `email_password`  | `String(200)`    | Nullable                         | Sender app password             |

---

## SPEC-09: Error Handling & Logging

**Traceability:** FR12, NFR4, NFR11, NFR12

### 09.1 Error Handling Matrix

| Module              | Error                 | Severity | Fallback                                                |
|---------------------|-----------------------|----------|---------------------------------------------------------|
| Meeting Access      | `MeetingJoinError`    | Critical | Retry 3× → set status `"failed"` → abort pipeline.     |
| Meeting Access      | `PlatformNotSupported`| Critical | Abort immediately → log unsupported URL.                |
| Audio Capture       | `OBSConnectionError`  | Critical | Log → prompt user to check OBS → abort.                 |
| Audio Capture       | `EmptyRecordingError` | High     | Log → abort pipeline (nothing to transcribe).           |
| Transcription       | `STTRateLimitError`   | Medium   | Switch to fallback STT provider → retry once.           |
| Transcription       | `STTTimeoutError`     | Medium   | Exponential backoff retry (3 attempts max).             |
| Summarisation       | `LLMAPIError`         | Medium   | Retry 2× → fallback to basic extractive summary.        |
| Summarisation       | `EmptyTranscriptError`| High     | Skip summary → store transcript only → set `"failed"`.  |
| Output & Storage    | `EmailDeliveryError`  | Low      | Log failed recipients → continue with storage.          |
| Output & Storage    | `SheetsWriteError`    | Medium   | Fallback to local CSV → log warning.                    |
| Output & Storage    | `DatabaseWriteError`  | High     | Log → set status `"failed"`.                            |

### 09.2 Logging Specification

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

### 09.3 Session Log File

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

## SPEC-10: Test-Driven Development (TDD)

**Traceability:** All FR, All NFR, Development Methodology
**Methodology:** Red → Green → Refactor cycle for every module.

### 10.1 TDD Workflow

Every feature in SPEC-00 through SPEC-09 shall be developed using the following strict TDD cycle:

```
🔴 RED    → Write a failing test that defines the expected behaviour.
🟢 GREEN  → Write the minimum code to make the test pass.
🔵 REFACTOR → Improve code quality without changing behaviour. All tests must still pass.
```

**Rule:** No production code in `app.py`, `main.py`, `models.py`, `modules/*.py`, or `utils/*.py` may be written without a corresponding failing test first.

### 10.2 Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures (Flask test client, test DB, mock configs)
├── test_dashboard.py              # Tests for SPEC-00 (all routes)
├── test_models.py                 # Tests for SPEC-08 (Meeting & Settings models)
├── test_meeting_access.py         # Tests for SPEC-01 (MeetingAccess class)
├── test_audio_capture.py          # Tests for SPEC-02 (AudioCapture class)
├── test_transcription.py          # Tests for SPEC-03 (Transcription class)
├── test_summarisation.py          # Tests for SPEC-04 (Summarisation class)
├── test_output_storage.py         # Tests for SPEC-05 (OutputStorage class)
├── test_pipeline.py               # Tests for SPEC-06 (run_pipeline orchestrator)
├── test_config.py                 # Tests for SPEC-07 (Config loading)
└── test_logger.py                 # Tests for SPEC-09 (Logger setup)
```

### 10.3 Test Naming Convention

```python
# Pattern: test_{method_name}_{scenario}_{expected_result}

# Examples:
def test_detect_platform_google_meet_returns_google_meet():
def test_detect_platform_unsupported_link_raises_value_error():
def test_join_meeting_timeout_raises_meeting_join_error():
def test_transcribe_whisper_success_returns_normalised_result():
def test_send_email_smtp_failure_returns_failed_list():
def test_dashboard_get_returns_200():
def test_join_post_empty_link_flashes_error():
```

### 10.4 Shared Test Fixtures (`conftest.py`)

```python
import pytest
from app import app as flask_app
from models import db

@pytest.fixture
def app():
    """Create a test Flask application with an in-memory database."""
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()

@pytest.fixture
def client(app):
    """Provide a Flask test client."""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Provide a clean database session for each test."""
    with app.app_context():
        yield db.session
        db.session.rollback()

@pytest.fixture
def sample_transcript():
    """Provide a sample TranscriptResult for testing."""
    return {
        "full_text": "Hello everyone. Let's discuss the project timeline...",
        "segments": [
            {"speaker": "Speaker 1", "start_time": 0.0, "end_time": 5.0, "text": "Hello everyone."},
            {"speaker": "Speaker 2", "start_time": 5.5, "end_time": 12.0, "text": "Let's discuss the project timeline."}
        ],
        "language": "en",
        "duration_seconds": 1800,
        "provider": "whisper",
        "diarisation_available": True
    }

@pytest.fixture
def sample_report():
    """Provide a sample MeetingReport for testing."""
    return {
        "summary": "Meeting discussed the project timeline and milestones.",
        "action_items": [{"assignee": "Alice", "task": "Update docs", "deadline": "2026-03-20"}],
        "decisions": ["Approved new timeline"],
        "follow_up": ["Review budget"],
        "speaker_stats": None
    }
```

### 10.5 Per-Module TDD Test Specifications

#### 10.5.1 SPEC-00 Tests: Dashboard (`test_dashboard.py`) **[M]**

| Test Case                                          | Type        | Asserts                                                  |
|----------------------------------------------------|-------------|----------------------------------------------------------|
| `test_dashboard_get_returns_200`                   | Unit        | `GET /` returns status 200.                              |
| `test_dashboard_renders_meeting_form`              | Unit        | Response contains `meeting_link` input and `Join` button.|
| `test_join_post_valid_data_redirects`              | Unit        | `POST /join` with valid data returns 302.                |
| `test_join_post_empty_link_flashes_error`          | Unit        | `POST /join` with empty link returns error flash.        |
| `test_join_post_empty_emails_flashes_error`        | Unit        | `POST /join` with empty emails returns error flash.      |
| `test_history_get_returns_200`                     | Unit        | `GET /history` returns status 200.                       |
| `test_history_lists_meetings_desc_order`           | Integration | Meetings appear in descending date order.                |
| `test_meeting_detail_valid_id_returns_200`         | Unit        | `GET /history/<id>` with valid ID returns 200.           |
| `test_meeting_detail_invalid_id_returns_404`       | Unit        | `GET /history/<id>` with invalid ID returns 404.         |
| `test_settings_get_returns_200`                    | Unit        | `GET /settings` returns status 200.                      |
| `test_settings_post_saves_storage_backend`         | Integration | `POST /settings` updates `storage_backend` in DB.        |
| `test_settings_post_saves_stt_provider`            | Integration | `POST /settings` updates `stt_provider` in DB.           |

**Example test (Red phase):**

```python
def test_dashboard_get_returns_200(client):
    """SPEC-00: GET / should render the dashboard page."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"meeting_link" in response.data
    assert b"Join Meeting" in response.data or b"Join" in response.data
```

#### 10.5.2 SPEC-01 Tests: Meeting Access (`test_meeting_access.py`) **[M]**

| Test Case                                          | Type        | Asserts                                                  |
|----------------------------------------------------|-------------|----------------------------------------------------------|
| `test_detect_platform_google_meet`                 | Unit        | Returns `"google_meet"` for a Google Meet URL.           |
| `test_detect_platform_zoom`                        | Unit        | Returns `"zoom"` for a Zoom URL.                         |
| `test_detect_platform_teams`                       | Unit        | Returns `"teams"` for a Teams URL.                       |
| `test_detect_platform_unsupported_raises`          | Unit        | Raises `ValueError` for an unsupported URL.              |
| `test_init_browser_creates_driver`                 | Unit (mock) | `webdriver.Chrome` is called with correct options.       |
| `test_join_sets_detected_platform`                 | Unit (mock) | `self.detected_platform` is set after calling `join()`.  |
| `test_join_timeout_raises_meeting_join_error`      | Unit (mock) | Raises `MeetingJoinError` after timeout.                 |
| `test_leave_quits_driver`                          | Unit (mock) | `driver.quit()` is called.                               |

**Example test (Red phase):**

```python
from modules.meeting_access import MeetingAccess

def test_detect_platform_google_meet():
    """SPEC-01: Google Meet links should be detected correctly."""
    ma = MeetingAccess.__new__(MeetingAccess)  # skip __init__
    result = ma._detect_platform("https://meet.google.com/abc-defg-hij")
    assert result == "google_meet"

def test_detect_platform_unsupported_raises():
    """SPEC-01: Unsupported platforms should raise ValueError."""
    ma = MeetingAccess.__new__(MeetingAccess)
    with pytest.raises(ValueError, match="Unsupported meeting platform"):
        ma._detect_platform("https://example.com/meeting")
```

#### 10.5.3 SPEC-02 Tests: Audio Capture (`test_audio_capture.py`) **[M]**

| Test Case                                          | Type        | Asserts                                                  |
|----------------------------------------------------|-------------|----------------------------------------------------------|
| `test_init_connects_to_obs`                        | Unit (mock) | `ReqClient()` is called with correct host/port/password. |
| `test_init_connection_failure_raises`               | Unit (mock) | Raises `OBSConnectionError` on connection failure.       |
| `test_start_calls_start_record`                    | Unit (mock) | `client.start_record()` is called.                       |
| `test_stop_returns_file_path`                      | Unit (mock) | Returns a valid file path string.                        |
| `test_stop_empty_file_raises`                      | Unit (mock) | Raises `EmptyRecordingError` for 0-byte file.            |
| `test_healthcheck_obs_running_returns_true`        | Unit (mock) | Returns `True` when OBS responds to `get_version()`.     |
| `test_healthcheck_obs_not_running_returns_false`   | Unit (mock) | Returns `False` when OBS is unreachable.                 |

#### 10.5.4 SPEC-03 Tests: Transcription (`test_transcription.py`) **[M]**

| Test Case                                          | Type        | Asserts                                                  |
|----------------------------------------------------|-------------|----------------------------------------------------------|
| `test_transcribe_whisper_returns_normalised`       | Unit (mock) | Output matches `TranscriptResult` schema.                |
| `test_transcribe_deepgram_returns_normalised`      | Unit (mock) | Output matches `TranscriptResult` schema.                |
| `test_transcribe_assemblyai_returns_normalised`    | Unit (mock) | Output matches `TranscriptResult` schema.                |
| `test_transcribe_unknown_provider_raises`          | Unit        | Raises `ValueError` for unknown provider.                |
| `test_normalise_whisper_response`                  | Unit        | Raw Whisper response is normalised correctly.            |
| `test_normalise_deepgram_response_with_diarisation`| Unit        | Diarisation data is extracted correctly.                  |
| `test_transcribe_timeout_retries`                  | Unit (mock) | Retries 3 times with exponential backoff.                |
| `test_transcribe_rate_limit_switches_provider`     | Unit (mock) | Falls back to alternative provider on 429.               |

#### 10.5.5 SPEC-04 Tests: Summarisation (`test_summarisation.py`) **[M]**

| Test Case                                          | Type        | Asserts                                                  |
|----------------------------------------------------|-------------|----------------------------------------------------------|
| `test_generate_report_returns_all_sections`        | Unit (mock) | Report contains `summary`, `action_items`, `decisions`.  |
| `test_generate_summary_calls_llm`                  | Unit (mock) | OpenAI API is called with correct prompt.                |
| `test_extract_action_items_parses_json`            | Unit        | Action items JSON is parsed into list of dicts.          |
| `test_extract_decisions_returns_list`              | Unit        | Decisions are returned as a list of strings.             |
| `test_analyse_participation_with_diarisation`      | Unit        | Speaker stats are computed correctly.                    |
| `test_analyse_participation_no_diarisation`        | Unit        | Returns `None` when no speaker data.                     |
| `test_empty_transcript_raises`                     | Unit        | Raises `EmptyTranscriptError` for empty text.            |
| `test_llm_api_error_retries`                       | Unit (mock) | Retries on LLM API failure.                              |

#### 10.5.6 SPEC-05 Tests: Output & Storage (`test_output_storage.py`) **[M]**

| Test Case                                          | Type        | Asserts                                                  |
|----------------------------------------------------|-------------|----------------------------------------------------------|
| `test_send_email_success`                          | Unit (mock) | SMTP `sendmail` is called with correct recipients.       |
| `test_send_email_failure_logs_failed`              | Unit (mock) | Failed recipients are logged.                            |
| `test_store_database_writes_meeting`               | Integration | Meeting data is written to the SQLite database.          |
| `test_store_sheets_appends_row`                    | Unit (mock) | `gspread` `append_row` is called with correct data.      |
| `test_store_sheets_failure_falls_back_to_csv`      | Unit (mock) | CSV file is created on Sheets write failure.             |
| `test_store_unknown_backend_raises`                | Unit        | Raises `ValueError` for unknown backend.                 |
| `test_format_email_body_html`                      | Unit        | Email body contains HTML with summary and action items.  |

#### 10.5.7 SPEC-06 Tests: Pipeline (`test_pipeline.py`) **[M]**

| Test Case                                          | Type        | Asserts                                                  |
|----------------------------------------------------|-------------|----------------------------------------------------------|
| `test_pipeline_happy_path_completes`               | Integration | All 7 steps execute; status = `"completed"`.             |
| `test_pipeline_join_failure_sets_failed`            | Integration | Status = `"failed"` when MeetingJoinError occurs.        |
| `test_pipeline_creates_meeting_record`             | Integration | A `Meeting` row exists in DB after pipeline starts.      |
| `test_pipeline_updates_status_at_each_step`        | Integration | Status column updates at each pipeline step.             |
| `test_pipeline_error_leaves_meeting`               | Integration | `leave()` is called even when pipeline fails.            |

#### 10.5.8 SPEC-07 Tests: Configuration (`test_config.py`) **[M]**

| Test Case                                          | Type        | Asserts                                                  |
|----------------------------------------------------|-------------|----------------------------------------------------------|
| `test_config_loads_defaults`                       | Unit        | Default values are set when `.env` is absent.            |
| `test_config_loads_env_variables`                  | Unit        | Values from `.env` override defaults.                    |
| `test_config_stt_provider_default_whisper`         | Unit        | `STT_PROVIDER` defaults to `"whisper"`.                  |
| `test_config_obs_port_is_integer`                  | Unit        | `OBS_PORT` is parsed as an integer.                      |

#### 10.5.9 SPEC-08 Tests: Models (`test_models.py`) **[M]**

| Test Case                                          | Type        | Asserts                                                  |
|----------------------------------------------------|-------------|----------------------------------------------------------|
| `test_create_meeting_record`                       | Integration | Meeting is created and retrievable from DB.              |
| `test_meeting_default_status_pending`              | Unit        | New meetings default to `status="pending"`.              |
| `test_meeting_status_lifecycle`                    | Integration | Status updates through full lifecycle.                   |
| `test_settings_singleton`                          | Integration | Only one Settings row exists at a time.                  |
| `test_settings_default_storage_database`           | Unit        | Default `storage_backend` is `"database"`.               |

### 10.6 Mocking Strategy

| External Dependency   | Mock Approach                                                   |
|-----------------------|-----------------------------------------------------------------|
| Selenium WebDriver    | `unittest.mock.patch("selenium.webdriver.Chrome")`              |
| OBS WebSocket         | `unittest.mock.patch("obsws_python.ReqClient")`                 |
| OpenAI API            | `unittest.mock.patch("openai.OpenAI")`                          |
| Deepgram API          | `unittest.mock.patch("deepgram.Deepgram")`                      |
| AssemblyAI API        | `unittest.mock.patch("assemblyai.Transcriber")`                 |
| SMTP (email)          | `unittest.mock.patch("smtplib.SMTP_SSL")`                       |
| Google Sheets API     | `unittest.mock.patch("gspread.authorize")`                      |
| File system (os/io)   | `tmp_path` fixture or `unittest.mock.patch("builtins.open")`    |

**Principle:** All external services are mocked in unit tests. Only integration tests with dedicated test environments may call real APIs.

### 10.7 Test Execution

```bash
# Run all tests (TDD cycle — run frequently)
python -m pytest tests/ -v

# Run a specific module's tests
python -m pytest tests/test_meeting_access.py -v

# Run with coverage report
python -m pytest tests/ --cov=modules --cov=. --cov-report=html --cov-report=term-missing

# Run only failing tests (fast feedback loop)
python -m pytest tests/ --lf -v

# Run tests matching a keyword
python -m pytest tests/ -k "platform" -v
```

### 10.8 Coverage Requirements

| Module                | Minimum Coverage | Target Coverage |
|-----------------------|------------------|-----------------|
| `app.py` (routes)     | 80%              | 90%             |
| `models.py`           | 90%              | 100%            |
| `modules/meeting_access.py` | 75%       | 85%             |
| `modules/audio_capture.py`  | 75%       | 85%             |
| `modules/transcription.py`  | 80%       | 90%             |
| `modules/summarisation.py`  | 80%       | 90%             |
| `modules/output_storage.py` | 80%       | 90%             |
| `main.py` (pipeline)  | 75%              | 85%             |
| `config.py`           | 90%              | 100%            |
| `utils/logger.py`     | 80%              | 90%             |
| **Overall**           | **80%**          | **90%**         |

### 10.9 TDD Workflow Checklist (Per Feature)

| Step | Action                                                            | Done |
|------|-------------------------------------------------------------------|------|
| 1    | Identify the feature/function from SPEC-XX.                      | ☐    |
| 2    | 🔴 Write one or more failing tests in `tests/test_*.py`.          | ☐    |
| 3    | Run `pytest` — confirm the test(s) fail (Red).                    | ☐    |
| 4    | 🟢 Write the minimum production code to pass the test(s).         | ☐    |
| 5    | Run `pytest` — confirm the test(s) pass (Green).                  | ☐    |
| 6    | 🔵 Refactor code for quality. Run `pytest` — all tests still pass.| ☐    |
| 7    | Repeat for the next feature/function.                            | ☐    |
| 8    | Check coverage — `pytest --cov` meets minimum threshold.         | ☐    |

### 10.10 Error Codes

| Code    | Name                    | Trigger                                        |
|---------|-------------------------|------------------------------------------------|
| TD-001  | `TestNotWrittenFirst`   | Production code committed without failing test. |
| TD-002  | `CoverageBelowMinimum`  | Module coverage drops below minimum threshold.  |

---

## Appendix A: Acceptance Criteria Checklist

| SPEC   | Criteria                                                                              | Verified |
|--------|---------------------------------------------------------------------------------------|----------|
| SPEC-00| Dashboard page renders with meeting link input and Join button.                       | ☐        |
| SPEC-00| `/join` triggers the pipeline and redirects to dashboard.                             | ☐        |
| SPEC-00| History page lists meetings sorted by date descending.                                | ☐        |
| SPEC-00| Meeting detail page shows summary, transcript, and action items.                      | ☐        |
| SPEC-00| Settings page toggles storage backend and saves immediately.                          | ☐        |
| SPEC-00| Settings page allows STT provider selection.                                          | ☐        |
| SPEC-01| Bot joins Google Meet meeting and stays connected.                                    | ☐        |
| SPEC-01| Bot joins Zoom meeting via web client and stays connected.                            | ☐        |
| SPEC-01| Bot joins MS Teams meeting and stays connected.                                       | ☐        |
| SPEC-01| Bot detects meeting end and returns control.                                          | ☐        |
| SPEC-02| OBS starts recording when pipeline begins.                                            | ☐        |
| SPEC-02| OBS stops recording and outputs a valid audio file.                                   | ☐        |
| SPEC-02| Healthcheck detects OBS not running.                                                  | ☐        |
| SPEC-03| Whisper API transcribes audio and returns normalised output.                          | ☐        |
| SPEC-03| Deepgram transcribes audio with diarisation.                                          | ☐        |
| SPEC-03| AssemblyAI transcribes audio with speaker labels.                                     | ☐        |
| SPEC-03| Provider switching works when primary provider fails.                                 | ☐        |
| SPEC-04| LLM generates structured summary with all 5 sections.                                | ☐        |
| SPEC-04| Action items are extracted as structured JSON.                                        | ☐        |
| SPEC-04| Participation analysis produces speaker statistics.                                   | ☐        |
| SPEC-04| Summary generated within 2 minutes for 30-minute meeting.                            | ☐        |
| SPEC-05| Email delivered to all recipients with HTML body.                                     | ☐        |
| SPEC-05| Data stored in SQLite when backend = "database".                                      | ☐        |
| SPEC-05| Data stored in Google Sheets when backend = "google_sheets".                          | ☐        |
| SPEC-05| Fallback to CSV when Google Sheets write fails.                                       | ☐        |
| SPEC-06| Full pipeline completes within 10 minutes post-meeting.                               | ☐        |
| SPEC-06| Meeting record status updates live in database.                                       | ☐        |
| SPEC-06| Pipeline handles errors gracefully without crashing the server.                       | ☐        |
| SPEC-08| Database tables created automatically on first run.                                   | ☐        |
| SPEC-09| Session log JSON file produced for each meeting.                                      | ☐        |
| SPEC-09| Errors logged with correct severity levels.                                           | ☐        |
| SPEC-10| All test files exist before corresponding module implementation.                      | ☐        |
| SPEC-10| TDD Red-Green-Refactor cycle followed for every module.                               | ☐        |
| SPEC-10| Overall test coverage ≥ 80%.                                                           | ☐        |
| SPEC-10| All mocked external dependencies (APIs, SMTP, OBS, Sheets).                           | ☐        |
| SPEC-10| `conftest.py` provides shared fixtures for test client and test DB.                   | ☐        |
