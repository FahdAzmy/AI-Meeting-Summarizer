# SPEC-05: Output & Storage Module

| Field            | Details                                        |
|------------------|------------------------------------------------|
| **File**         | `modules/output_storage.py`                    |
| **Class**        | `OutputStorage`                                |
| **Traceability** | FR8, FR9, NFR7, NFR8                           |
| **Framework**    | FastAPI (async) + Beanie ODM + MongoDB         |
| **Version**      | 1.0                                            |
| **Date**         | March 12, 2026                                 |

---

## 05.1 Class Interface

```python
class OutputStorage:
    def __init__(self, backend: str = "database") -> None
    
    async def send_email(self, recipients: list[str], report: dict) -> dict
    async def send_failure_email(self, recipients: list[str], **kwargs) -> dict
    async def store(self, meeting: Meeting, report: dict, transcript: dict) -> None
    async def _store_to_database(self, meeting: Meeting, report: dict, transcript: dict) -> None
    async def _store_to_sheets(self, report: dict, transcript: dict) -> None
    def _format_email_body(self, report: dict) -> str
```

> **Note:** All I/O methods are `async` to match FastAPI's async architecture.

---

## 05.2 Storage Backend Router

```python
async def store(self, meeting: Meeting, report: dict, transcript: dict) -> None:
    if self.backend == "database":
        await self._store_to_database(meeting, report, transcript)
    elif self.backend == "google_sheets":
        await self._store_to_sheets(report, transcript)
    else:
        raise ValueError(f"Unknown storage backend: {self.backend}")
```

---

## 05.3 Email Specification

| Property         | Value                                                       |
|------------------|-------------------------------------------------------------|
| Protocol         | SMTP over SSL (port 465)                                    |
| SMTP Host        | `smtp.gmail.com` (configurable)                             |
| Library          | `aiosmtplib` (async SMTP client)                            |
| Sender           | `Config.EMAIL_SENDER` (or from Settings collection)         |
| Content-Type     | `multipart/alternative` (HTML body)                         |
| Subject format   | `"Meeting Summary — {platform} — {date}"`                   |

**Async email sending:**

```python
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_email(self, recipients: list[str], report: dict) -> dict:
    sent, failed = [], []
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Meeting Summary — {report['platform']} — {report['date']}"
    msg["From"] = self.email_sender
    msg.attach(MIMEText(self._format_email_body(report), "html"))

    for recipient in recipients:
        try:
            msg["To"] = recipient
            await aiosmtplib.send(
                msg,
                hostname="smtp.gmail.com",
                port=465,
                use_tls=True,
                username=self.email_sender,
                password=self.email_password,
            )
            sent.append(recipient)
        except Exception as e:
            failed.append(recipient)
            logger.warning(f"Email to {recipient} failed: {e}")

    return {"sent": sent, "failed": failed, "total": len(recipients)}
```

**Email body structure (HTML):**
1. Meeting overview header
2. Key discussion points
3. Action items table
4. Decisions list
5. Link to full transcript (if accessible)

---

## 05.4 Database Storage Specification (MongoDB)

When `backend == "database"`, update the `Meeting` document via Beanie:

```python
async def _store_to_database(self, meeting: Meeting, report: dict, transcript: dict) -> None:
    meeting.summary = report["summary"]
    meeting.action_items = [ActionItem(**item) for item in report["action_items"]]
    meeting.decisions = report["decisions"]
    meeting.transcript = transcript["full_text"]
    meeting.speaker_stats = SpeakerStats(**report["speaker_stats"]) if report.get("speaker_stats") else None
    meeting.duration_minutes = int(transcript["duration_seconds"] // 60)
    meeting.status = MeetingStatus.COMPLETED
    await meeting.save()
```

| Meeting Field       | Source                                           |
|---------------------|--------------------------------------------------|
| `summary`           | `report["summary"]`                              |
| `action_items`      | `report["action_items"]` → embedded `ActionItem` |
| `decisions`         | `report["decisions"]` → embedded list            |
| `transcript`        | `transcript["full_text"]`                        |
| `speaker_stats`     | `report["speaker_stats"]` → embedded `SpeakerStats` |
| `duration_minutes`  | `transcript["duration_seconds"] // 60`           |
| `status`            | `MeetingStatus.COMPLETED`                        |

> **Key difference from SQL:** No `json.dumps()` needed — MongoDB stores arrays and objects natively.

---

## 05.5 Google Sheets Storage Specification

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

> **Note:** Even when using Google Sheets as the storage backend, the `Meeting` document in MongoDB is **always** updated (for the history page). The Sheets write is an *additional* export.

---

## 05.6 Error Codes

| Code    | Name                     | Trigger                                       |
|---------|--------------------------|-----------------------------------------------|
| OS-001  | `EmailDeliveryError`     | SMTP connection failed or send error.         |
| OS-002  | `SheetsWriteError`       | Google Sheets API returned error.             |
| OS-003  | `DatabaseWriteError`     | Beanie/MongoDB save failed.                   |
| OS-004  | `InvalidBackendError`    | Unknown `storage_backend` value.              |

**Fallback:** If Google Sheets write fails → fall back to local CSV file at `./summaries/{session_id}.csv`.

---

## 05.7 Acceptance Criteria

| #  | Criteria                                                             | Verified |
|----|----------------------------------------------------------------------|----------|
| 1  | Email delivered to all recipients with HTML body (async).            | ☐        |
| 2  | Data stored in MongoDB when backend = "database".                    | ☐        |
| 3  | Data stored in Google Sheets when backend = "google_sheets".         | ☐        |
| 4  | MongoDB always updated regardless of storage backend selection.      | ☐        |
| 5  | Fallback to CSV when Google Sheets write fails.                      | ☐        |
