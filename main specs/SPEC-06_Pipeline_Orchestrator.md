# SPEC-06: Pipeline Orchestrator

| Field            | Details                                       |
|------------------|-----------------------------------------------|
| **File**         | `main.py`                                     |
| **Function**     | `run_pipeline()`                              |
| **Framework**    | FastAPI (async) + Beanie ODM + MongoDB        |
| **Traceability** | All FR, NFR1, NFR9                            |
| **Version**      | 1.0                                           |
| **Date**         | March 12, 2026                                |

---

## 06.1 Function Signature

```python
async def run_pipeline(
    meeting_link: str,
    participant_emails: list[str],
    storage_backend: str = "database"
) -> None
```

> **Note:** The pipeline is `async` to match FastAPI's architecture and use Beanie's async database operations.

---

## 06.2 Pipeline Steps

| Step | Action                  | Module Used       | Status Value    | Error Handling                      |
|------|-------------------------|-------------------|-----------------|-------------------------------------|
| 1    | Join meeting            | `MeetingAccess`   | `"joining"`     | Retry 3× → failure email → abort   |
| 2    | Start recording         | `AudioCapture`    | `"recording"`   | Log + abort                         |
| 3    | Wait for meeting end    | `MeetingAccess`   | `"recording"`   | Monitor connection                  |
| 4    | Stop recording          | `AudioCapture`    | `"recording"`   | Log partial                         |
| 5    | Transcribe audio        | `Transcription`   | `"transcribing"`| Retry / switch provider             |
| 6    | Generate summary        | `Summarisation`   | `"summarising"` | Retry → basic extraction fallback  |
| 7    | Send email + store data | `OutputStorage`   | `"delivering"`  | Log failed recipients               |
| ✓    | Complete                | —                 | `"completed"`   | —                                   |
| ✗    | Failure at any step     | —                 | `"failed"`      | Error logged; `Meeting.status` set  |

---

## 06.3 Meeting Record Tracking

A `Meeting` document is inserted into MongoDB at Step 1 and progressively updated at each step via Beanie's async `save()`:

```python
# Create meeting record
meeting_record = Meeting(
    session_id=session_id,
    meeting_link=meeting_link,
    participants=participant_emails,
    storage_backend=storage_backend,
    status=MeetingStatus.JOINING,
)
await meeting_record.insert()

# Update status at each step
meeting_record.status = MeetingStatus.RECORDING
await meeting_record.save()
```

This enables the Next.js dashboard History page to show live status for in-progress meetings.

---

## 06.4 Background Task Execution

FastAPI runs the pipeline as a **background task** using `BackgroundTasks` or `asyncio.create_task()`:

```python
from fastapi import BackgroundTasks

@app.post("/api/join")
async def join_meeting(request: JoinRequest, background_tasks: BackgroundTasks):
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    background_tasks.add_task(run_pipeline, request.meeting_link, request.emails, storage_backend)
    return {"session_id": session_id}
```

### Concurrency Notes
- Each pipeline run executes as an async background task.
- Blocking operations (Selenium, OBS) run in an executor via `asyncio.to_thread()`.
- Beanie database operations are natively async — no special handling needed.
- No shared mutable state between concurrent pipelines.
- Sequential meeting processing (NFR9) — if system resources are limited, a queue can be used.

---

## 06.5 Acceptance Criteria

| #  | Criteria                                                             | Verified |
|----|----------------------------------------------------------------------|----------|
| 1  | Full pipeline completes within 10 minutes post-meeting.              | ☐        |
| 2  | Meeting document status updates live in MongoDB.                     | ☐        |
| 3  | Pipeline handles errors gracefully without crashing the FastAPI server. | ☐     |
| 4  | Blocking operations (Selenium, OBS) do not block the event loop.     | ☐        |
