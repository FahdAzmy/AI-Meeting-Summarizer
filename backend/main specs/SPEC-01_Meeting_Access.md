# SPEC-01: Meeting Access Module

| Field            | Details                                  |
|------------------|------------------------------------------|
| **File**         | `modules/meeting_access.py`              |
| **Class**        | `MeetingAccess`                          |
| **Traceability** | FR1, FR2, NFR5                           |
| **Version**      | 1.0                                      |
| **Date**         | March 12, 2026                           |

---

## 01.1 Class Interface

```python
class MeetingAccess:
    detected_platform: str          # "google_meet" | "zoom" | "teams"
    
    def __init__(self) -> None
    def join(self, link: str) -> None
    def wait_until_end(self) -> None
    def leave(self) -> None
```

---

## 01.2 Method Specifications

### `__init__()` **[M]**
- Initialises Chrome via `webdriver-manager` with the following flags:
  - `--disable-notifications`
  - `--use-fake-ui-for-media-stream`
  - `--use-fake-device-for-media-stream`
  - `--disable-blink-features=AutomationControlled`
- Stores the `WebDriver` instance as `self.driver`.

### `join(link: str)` **[M]**
1. Call `_detect_platform(link)` → sets `self.detected_platform`.
2. Navigate to `link`.
3. Execute platform-specific join sequence:

| Platform       | Join Sequence                                                                  | Timeout |
|----------------|--------------------------------------------------------------------------------|---------|
| Google Meet    | Dismiss pre-join → mute mic → mute cam → click "Join now"                     | 60s     |
| Zoom (Web)     | Enter display name → click "Join" → handle waiting room                        | 90s     |
| MS Teams       | Click "Continue on this browser" → mute mic → mute cam → click "Join now"     | 90s     |

4. On success → log join timestamp.
5. On failure (timeout or element not found) → **retry** (see policy below).
6. On **final failure** (all retries exhausted) → trigger **Failure Notification Flow** (see §01.6):
   - Set `Meeting.status = "failed"` in the database.
   - Send failure notification email to all participants.
   - Push failure status to the dashboard via `/api/status/:session_id`.
   - Raise `MeetingJoinError` to abort the pipeline.

**Retry policy:** 3 attempts, 10-second delay between retries.

### `wait_until_end()` **[M]**
- Poll the meeting page every 30 seconds.
- Detect meeting-ended signals:
  - Google Meet: "You've left the meeting" or "Meeting ended" header.
  - Zoom: browser URL changes or disconnect dialog.
  - Teams: "You left the meeting" banner.
- On detection → return control to the pipeline.

### `leave()` **[M]**
- Click the platform's "Leave" button (if still in meeting).
- Call `self.driver.quit()` to close the browser instance.

---

## 01.3 Platform Detection

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

---

## 01.4 CSS Selectors (Configuration-Driven)

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

---

## 01.5 Error Codes

| Code    | Name                 | Trigger                                           |
|---------|----------------------|---------------------------------------------------|
| MA-001  | `MeetingJoinError`   | Failed to join after 3 retries.                   |
| MA-002  | `PlatformNotSupported` | Link does not match any supported platform.     |
| MA-003  | `BrowserInitError`   | Chrome/WebDriver failed to initialise.            |
| MA-004  | `WaitingRoomTimeout` | Host did not admit within 5 minutes.              |
| MA-005  | `JoinFailureNotified`| Join failed — failure email sent + dashboard notified. |

---

## 01.6 Failure Notification Specification **[M]**

When the bot **cannot join the meeting** (after exhausting all retries), the system must perform two notification actions before aborting:

### Failure Flow

```
join() fails after 3 retries
        │
        ├──→ 1. Update Meeting record  →  status = "failed"
        │                                  failure_reason = "Could not join meeting"
        │
        ├──→ 2. Send Failure Email     →  to all participant emails
        │                                  via OutputStorage.send_failure_email()
        │
        ├──→ 3. Push Dashboard Notification  →  via /api/status/:session_id
        │                                       status = "failed"
        │                                       message = "Failed to join meeting"
        │
        └──→ 4. Raise MeetingJoinError →  pipeline aborts
```

### 01.6.1 Failure Email **[M]**

When the join fails, an email is sent to all participants listed in the meeting request.

| Property         | Value                                                             |
|------------------|-------------------------------------------------------------------|
| Recipients       | All participant emails from the join request.                     |
| Subject          | `"⚠️ Meeting Assistant — Failed to Join Meeting"`                 |
| Sender           | `Config.EMAIL_SENDER` (or from Settings table)                    |
| Content-Type     | `text/html`                                                       |

**Email body content:**

```html
<div style="font-family: sans-serif; max-width: 600px;">
    <h2 style="color: #e74c3c;">⚠️ Meeting Join Failed</h2>
    <p>The AI Meeting Assistant was <strong>unable to join</strong> the scheduled meeting.</p>
    
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td><strong>Meeting Link:</strong></td>
            <td><a href="{meeting_link}">{meeting_link}</a></td>
        </tr>
        <tr>
            <td><strong>Platform:</strong></td>
            <td>{platform}</td>
        </tr>
        <tr>
            <td><strong>Attempted At:</strong></td>
            <td>{timestamp}</td>
        </tr>
        <tr>
            <td><strong>Retries:</strong></td>
            <td>{retry_count} / 3</td>
        </tr>
        <tr>
            <td><strong>Reason:</strong></td>
            <td>{failure_reason}</td>
        </tr>
    </table>
    
    <p style="margin-top: 20px; color: #666;">
        Please try again by submitting the meeting link on the dashboard,
        or join the meeting manually.
    </p>
</div>
```

**Failure reasons (included in email):**

| Reason                       | When                                               |
|------------------------------|----------------------------------------------------|
| `"Join button not found"`    | Platform UI changed; CSS selector broken.          |
| `"Waiting room timeout"`     | Host did not admit within 5 minutes.               |
| `"Browser crashed"`          | Chrome/WebDriver encountered a fatal error.        |
| `"Unsupported platform"`     | Meeting link is not Google Meet, Zoom, or Teams.   |
| `"Connection timeout"`       | Page did not load within timeout.                  |

### 01.6.2 Dashboard Notification **[M]**

The pipeline updates the meeting status in the database, which the Next.js dashboard reads via the status API.

**Status API response on failure:**

```json
{
    "session_id": "20260312_143015",
    "status": "failed",
    "step": 1,
    "total_steps": 7,
    "message": "Failed to join meeting: Join button not found after 3 retries",
    "failure": {
        "error_code": "MA-001",
        "error_name": "MeetingJoinError",
        "reason": "Join button not found",
        "retries_attempted": 3,
        "timestamp": "2026-03-12T14:31:45Z",
        "email_notification_sent": true
    }
}
```

**Frontend behaviour (`StatusPanel` component in Next.js):**

| Status      | UI Behaviour                                                              |
|-------------|--------------------------------------------------------------------------|
| `joining`   | Show spinner + "Joining meeting..."                                      |
| `failed`    | Show ❌ red alert banner with failure reason.                             |
|             | Display: "Failed to join — {reason}"                                     |
|             | Show: "A notification email has been sent to all participants."          |
|             | Show: "Retry" button → re-submits the same meeting link.                |
| `completed` | Show ✅ green success banner + link to meeting detail page.              |

### 01.6.3 Implementation in Pipeline (`main.py`)

```python
# Inside run_pipeline() — Step 1: Join Meeting
try:
    meeting.join(meeting_link)
except MeetingJoinError as e:
    meeting_record.status = "failed"
    meeting_record.failure_reason = str(e)
    db.session.commit()
    
    # Send failure notification email
    from modules.output_storage import OutputStorage
    output = OutputStorage(backend=storage_backend)
    output.send_failure_email(
        recipients=participant_emails,
        meeting_link=meeting_link,
        platform=meeting.detected_platform or "unknown",
        reason=str(e),
        retry_count=3
    )
    
    logger.error(f"Join failed — notification email sent to {len(participant_emails)} participants")
    raise  # Re-raise to abort pipeline
```

---

## 01.7 Acceptance Criteria

| #  | Criteria                                                                        | Verified |
|----|---------------------------------------------------------------------------------|----------|
| 1  | Bot joins Google Meet meeting and stays connected.                              | ☐        |
| 2  | Bot joins Zoom meeting via web client and stays connected.                      | ☐        |
| 3  | Bot joins MS Teams meeting and stays connected.                                 | ☐        |
| 4  | Bot detects meeting end and returns control.                                    | ☐        |
| 5  | On join failure, a failure email is sent to all participants.                    | ☐        |
| 6  | Failure email includes meeting link, platform, timestamp, and failure reason.    | ☐        |
| 7  | On join failure, the dashboard shows a red alert with the failure reason.        | ☐        |
| 8  | Dashboard shows "Retry" button after join failure.                              | ☐        |
| 9  | Dashboard shows confirmation that notification email was sent.                  | ☐        |
