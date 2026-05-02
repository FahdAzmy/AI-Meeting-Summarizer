# Feature Specification: Zoom Meeting SDK Integration

**Feature Branch**: `011-zoom-meeting-sdk`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: Replace fragile Selenium-based Zoom join flow with the official Zoom Meeting SDK (Web), providing a reliable, API-driven approach to joining Zoom meetings.

---

## Analysis: Current Approach vs Zoom Meeting SDK

### How We Currently Join Zoom Meetings (Selenium Approach)

The current `MeetingAccess._join_zoom()` method in `backend/modules/meeting_access.py` (lines 349–397) uses **Selenium WebDriver** to:

1. **Navigate** to the Zoom web client URL (`https://zoom.us/j/{meeting_id}`).
2. **Find the name field** (`#inputname`) and type "AI Meeting Assistant".
3. **Click the Join button** (`.preview-join-button`).
4. **Poll the waiting room** via XPath (`//p[contains(text(), 'Please wait')]`) with a 300-second timeout.

**Problems with this approach:**
- **Fragile CSS/XPath selectors**: Zoom frequently updates their web client UI. Selectors like `#inputname`, `.preview-join-button`, and `.zm-modal-body-title` break without warning.
- **Bot detection**: Zoom's web client actively detects and blocks automated browsers (Selenium headless, automation flags). Despite `--disable-blink-features=AutomationControlled`, join success rate is unreliable.
- **"Open Zoom" prompt interception**: The web client tries to redirect users to the desktop app. Intercepting this adds complexity and fails on some browser versions.
- **No native audio access**: Selenium cannot access the meeting's audio stream. We must rely on OBS screen/system audio capture running as a separate process, which is error-prone and resource-intensive.
- **No native event callbacks**: End-of-meeting detection requires continuous DOM polling (`_meeting_has_ended()`, `_is_alone_in_meeting()`) — expensive, unreliable, and lagging.

### What is the Zoom Meeting SDK?

The **Zoom Meeting SDK for Web** (`@zoom/meetingsdk`) is Zoom's official JavaScript SDK that embeds the complete Zoom meeting experience directly into a web page using **WebAssembly**. It provides:

- **Programmatic meeting join** via `ZoomMtg.join()` — no UI scraping.
- **Native event callbacks** for meeting start, end, participant join/leave.
- **Authenticated access** via JWT signatures — no password prompts or waiting room guessing.
- **Two rendering modes**: Client View (full Zoom UI) and Component View (modular, custom UI).

### What is a "Meeting SDK App"?

A **Meeting SDK App** (now called a **General App** with the Meeting SDK feature enabled) is an application registered in the [Zoom App Marketplace](https://marketplace.zoom.us/). Creating one gives you:

| Credential       | Purpose                                                        |
|-------------------|----------------------------------------------------------------|
| **Client ID**     | Identifies your app (public, safe for frontend)                |
| **Client Secret** | Signs JWT tokens for SDK authentication (backend-only, secret) |

**Steps to create:**
1. Log in to [marketplace.zoom.us](https://marketplace.zoom.us/) (Owner/Admin/Developer role).
2. Click **Develop** → **Build App** → choose **General App** → **Create**.
3. Fill in App Name + developer contact info on the **Basic Information** page.
4. Go to **Features** → **Embed** section → toggle **Meeting SDK** to **ON**.
5. Copy **Client ID** and **Client Secret** from the **App Credentials** section.
6. Use **Development** credentials for testing, switch to **Production** for release.

### How Joining Works with the Meeting SDK

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ARCHITECTURE FLOW                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    1. POST /api/zoom/signature     ┌──────────────┐   │
│  │ Frontend  │ ─────────────────────────────────→ │   Backend    │   │
│  │ (Next.js) │                                    │  (FastAPI)   │   │
│  │           │ ←───────────────────────────────── │              │   │
│  │           │    2. Return JWT signature          │  PyJWT sign  │   │
│  │           │                                    │  with secret │   │
│  │           │                                    └──────────────┘   │
│  │           │                                                       │
│  │           │    3. ZoomMtg.init() + ZoomMtg.join()                 │
│  │           │ ─────────────────────────────────→  Zoom Servers      │
│  │           │                                                       │
│  │           │    4. Meeting joined! SDK fires events                │
│  │           │ ←─────────────────────────────────  (WebAssembly)     │
│  └──────────┘                                                       │
│                                                                      │
│  5. Meeting ends → SDK fires 'meeting-ended' event                  │
│  6. Frontend calls POST /api/meetings/{id}/pipeline → orchestrator  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**JWT Signature payload** (generated server-side with `PyJWT`):

```python
import jwt, time

payload = {
    "appKey": ZOOM_SDK_CLIENT_ID,   # a.k.a. sdkKey
    "mn":     meeting_number,       # numeric meeting ID (e.g., "1234567890")
    "role":   0,                    # 0 = attendee, 1 = host
    "iat":    int(time.time()),
    "exp":    int(time.time()) + 7200,  # 2 hours
    "tokenExp": int(time.time()) + 7200,
}
signature = jwt.encode(payload, ZOOM_SDK_CLIENT_SECRET, algorithm="HS256")
```

**Frontend join call** (`@zoom/meetingsdk`):

```javascript
import { ZoomMtg } from '@zoom/meetingsdk';

ZoomMtg.preLoadWasm();
ZoomMtg.prepareWebSDK();

ZoomMtg.init({
  leaveUrl: '/meeting-ended',
  success: () => {
    ZoomMtg.join({
      signature: signatureFromBackend,
      meetingNumber: '1234567890',
      userName: 'AI Summarizer',
      passWord: meetingPassword,
      sdkKey: ZOOM_SDK_CLIENT_ID,
    });
  }
});
```

### Key Constraint: Audio Capture Strategy

> **The Zoom Meeting SDK for Web does NOT provide raw audio stream access.**

This means our existing OBS-based audio capture (`AudioCapture` module) remains necessary for recording. The SDK handles **joining the meeting reliably**, while OBS still records the system audio from the browser tab. This is the same pattern we use for Google Meet — Selenium joins, OBS records.

The difference is: **joining via SDK is far more reliable than Selenium scraping** because it uses official APIs instead of fragile DOM selectors.

### Comparison Summary

| Aspect                      | Current (Selenium)                     | Zoom Meeting SDK                          |
|-----------------------------|----------------------------------------|-------------------------------------------|
| **Join reliability**        | ~60-70% (selectors break often)        | ~99% (official API, no DOM scraping)      |
| **Bot detection risk**      | High (Selenium fingerprinting)         | None (official SDK, sanctioned by Zoom)   |
| **Meeting end detection**   | DOM polling every 5s (fragile)         | Native `meeting-ended` event callback     |
| **Waiting room handling**   | XPath polling (breaks on UI changes)   | SDK handles natively                      |
| **Auth method**             | None (guest join, often blocked)       | JWT signature (authenticated, trusted)    |
| **URL parsing**             | Regex pattern match only               | Extract meeting number + passcode         |
| **Setup complexity**        | Low (just Selenium)                    | Medium (Zoom Marketplace app + JWT)       |
| **Dependencies**            | `selenium`, `webdriver-manager`        | `@zoom/meetingsdk` (frontend), `PyJWT`    |
| **Audio capture**           | OBS (unchanged)                        | OBS (unchanged)                           |
| **Maintenance burden**      | High (selectors need constant updates) | Low (SDK versioned, backward-compatible)  |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Reliable Zoom Meeting Join via SDK (Priority: P1 - MVP)

Users need the AI Meeting Assistant to join Zoom meetings reliably using the official Meeting SDK instead of fragile Selenium browser automation. The SDK approach eliminates broken CSS selectors, bot detection blocks, and "Open Zoom App" prompt interception failures.

**Why this priority**: The current Selenium-based Zoom join has a ~60-70% success rate due to Zoom's frequent web client UI changes and active bot detection. This makes Zoom meetings unreliable for users, despite being the most popular meeting platform. Switching to the SDK is essential for production readiness.

**Independent Test**: Can be tested independently by creating a test Zoom meeting, generating a JWT signature on the backend, and verifying the frontend SDK successfully joins the meeting without any Selenium involvement.

**Acceptance Scenarios**:

1. **Given** a valid Zoom meeting link (e.g., `https://zoom.us/j/1234567890?pwd=abc123`), **When** the user submits it through the dashboard, **Then** the backend extracts the meeting number and passcode, generates a JWT signature, and the frontend SDK joins the meeting as "AI Summarizer" within 15 seconds.
2. **Given** a Zoom meeting with a waiting room enabled, **When** the SDK attendee enters the waiting room, **Then** the SDK natively handles the waiting state and joins automatically once the host admits the bot (or times out after 5 minutes with a `WaitingRoomTimeout` error).
3. **Given** the backend has valid `ZOOM_SDK_CLIENT_ID` and `ZOOM_SDK_CLIENT_SECRET` environment variables, **When** the `/api/zoom/signature` endpoint is called with a meeting number and role, **Then** it returns a valid JWT signature that the SDK accepts without errors.

---

### User Story 2 – Native Meeting End Detection (Priority: P1 - MVP)

Users rely on prompt post-meeting processing. The SDK provides native event callbacks for meeting end, replacing the fragile DOM-polling approach.

**Why this priority**: DOM polling for end-of-meeting signals is the second-largest source of pipeline failures after join failures. The SDK's event-driven architecture eliminates this entirely.

**Independent Test**: Can be tested by joining a test meeting via SDK, then ending the meeting from the host side, and verifying the `meeting-ended` callback fires within 5 seconds and triggers the pipeline progression.

**Acceptance Scenarios**:

1. **Given** the AI Summarizer is in an active Zoom meeting via the SDK, **When** the host ends the meeting, **Then** the SDK fires a native event that the frontend captures and sends a `POST /api/meetings/{id}/end` to the backend within 5 seconds.
2. **Given** the AI Summarizer is the only participant remaining, **When** the grace period (30 seconds) elapses, **Then** the frontend detects isolation (via SDK participant events) and triggers the meeting-end flow.

---

### User Story 3 – Zoom URL Parsing & Meeting Number Extraction (Priority: P1 - MVP)

The system must parse various Zoom URL formats to extract the meeting number and passcode needed by the SDK's `join()` function.

**Why this priority**: Users paste Zoom links in multiple formats. The SDK requires a numeric meeting number — the system must reliably extract this from any valid Zoom URL.

**Independent Test**: Unit tests with various URL formats (standard, vanity redirects, with/without passwords) verifying correct extraction.

**Acceptance Scenarios**:

1. **Given** a standard Zoom URL `https://zoom.us/j/1234567890?pwd=abc123`, **When** parsed, **Then** the system extracts meeting number `1234567890` and passcode `abc123`.
2. **Given** a Zoom URL with a subdomain `https://company.zoom.us/j/9876543210`, **When** parsed, **Then** the system extracts meeting number `9876543210` and empty passcode.
3. **Given** an invalid or unsupported Zoom URL format, **When** parsed, **Then** the system raises a descriptive error before attempting to join.

---

### User Story 4 – Fallback to Selenium for Non-SDK Platforms (Priority: P2)

Google Meet and MS Teams do not have equivalent embeddable SDKs. The system must maintain the existing Selenium join paths for those platforms while routing Zoom links through the new SDK path.

**Why this priority**: The system must remain multi-platform. The SDK integration must coexist with the existing Selenium infrastructure.

**Independent Test**: Submit a Google Meet link and verify it still uses the Selenium path. Submit a Zoom link and verify it uses the SDK path.

**Acceptance Scenarios**:

1. **Given** a Google Meet URL, **When** submitted to the pipeline, **Then** the system uses the existing `MeetingAccess._join_google_meet()` Selenium flow (no change).
2. **Given** a Zoom URL, **When** submitted to the pipeline, **Then** the system routes to the new SDK-based join flow instead of `MeetingAccess._join_zoom()`.
3. **Given** an MS Teams URL, **When** submitted to the pipeline, **Then** the system uses the existing `MeetingAccess._join_teams()` Selenium flow (no change).

### Edge Cases

- What happens if the Zoom SDK Client ID/Secret are not configured? → The system falls back to the existing Selenium approach with a warning log.
- What happens if the SDK fails to load (CDN/WASM error)? → Retry once, then fall back to Selenium with error logging.
- What happens if the meeting requires a ZAK token (authenticated-only meetings)? → Log a clear error: "This meeting requires Zoom authentication. Guest SDK join is not supported."
- What happens if the meeting number cannot be extracted from the URL (vanity URL)? → Return a descriptive error and do not attempt to join.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate a JWT signature on the backend using `ZOOM_SDK_CLIENT_ID` and `ZOOM_SDK_CLIENT_SECRET`, signed with HS256, containing `appKey`, `mn`, `role`, `iat`, `exp`, and `tokenExp` claims.
- **FR-002**: The system MUST expose a `POST /api/zoom/signature` endpoint that accepts `meeting_number` (string) and `role` (int, default 0) and returns `{ "signature": "<jwt>" }`.
- **FR-003**: The system MUST parse Zoom URLs to extract the numeric meeting number and optional passcode using regex: `https?://(?:[a-z0-9-]+\.)?zoom\.us/j/(\d+)(?:\?pwd=([a-zA-Z0-9]+))?`.
- **FR-004**: The frontend MUST install `@zoom/meetingsdk` and implement a Zoom meeting page/component that calls `ZoomMtg.init()` and `ZoomMtg.join()` with the backend-generated signature.
- **FR-005**: The frontend MUST listen for the SDK's meeting-end event and notify the backend via `POST /api/meetings/{id}/end` to trigger the post-meeting pipeline (transcription → summarisation → delivery).
- **FR-006**: The system MUST add `ZOOM_SDK_CLIENT_ID` and `ZOOM_SDK_CLIENT_SECRET` to the `Config` class in `backend/config/settings.py` as environment variables.
- **FR-007**: The pipeline orchestrator MUST detect Zoom URLs and route them through the SDK join path instead of the Selenium join path, while preserving Selenium for Google Meet and MS Teams.
- **FR-008**: The system MUST implement a graceful fallback to the existing Selenium Zoom join if the SDK credentials are not configured or the SDK fails to initialize.
- **FR-009**: The system MUST continue using OBS-based audio capture (`AudioCapture` module) for recording, as the Web SDK does not provide raw audio access.

### Non-Functional Requirements

- **NFR-001**: The JWT signature endpoint MUST respond in < 100ms.
- **NFR-002**: The SDK join flow MUST complete (from page load to in-meeting state) in < 15 seconds for meetings without waiting rooms.
- **NFR-003**: The `ZOOM_SDK_CLIENT_SECRET` MUST never be exposed in frontend code or API responses.

### Key Entities

- **Zoom SDK Credentials**: `ZOOM_SDK_CLIENT_ID` (public) + `ZOOM_SDK_CLIENT_SECRET` (private) — stored in `.env`.
- **JWT Signature**: Short-lived token (2h expiry) authorizing the SDK to join a specific meeting.
- **Meeting Number**: Numeric ID extracted from Zoom URLs (e.g., `1234567890` from `zoom.us/j/1234567890`).
- **Passcode**: Optional password extracted from Zoom URLs (`?pwd=...`).

---

## Implementation Plan

### Phase 1: Backend – Signature Generation & URL Parsing

**Files to modify/create:**

| Action   | File                                         | Description                                       |
|----------|----------------------------------------------|---------------------------------------------------|
| MODIFY   | `backend/config/settings.py`                 | Add `ZOOM_SDK_CLIENT_ID` and `ZOOM_SDK_CLIENT_SECRET` fields |
| MODIFY   | `backend/.env.example`                       | Add placeholder entries for Zoom SDK credentials  |
| MODIFY   | `backend/.env`                               | Add actual Zoom SDK credentials                   |
| MODIFY   | `backend/requirements.txt`                   | Add `pyjwt>=2.8.0`                               |
| NEW      | `backend/src/helpers/zoom_sdk.py`            | `generate_signature()` and `parse_zoom_url()` functions |
| NEW      | `backend/src/routes/zoom.py`                 | `POST /api/zoom/signature` endpoint              |
| MODIFY   | `backend/src/main.py`                        | Register the new Zoom router                     |
| NEW      | `backend/tests/unit/test_zoom_sdk.py`        | Unit tests for signature generation & URL parsing |

**Key implementation:**

```python
# backend/src/helpers/zoom_sdk.py

import re
import time
import jwt
from config.settings import Config

def generate_signature(meeting_number: str, role: int = 0) -> str:
    """Generate a JWT signature for the Zoom Meeting SDK."""
    cfg = Config()
    iat = int(time.time())
    exp = iat + 7200  # 2 hours

    payload = {
        "appKey": cfg.ZOOM_SDK_CLIENT_ID,
        "mn": meeting_number,
        "role": role,
        "iat": iat,
        "exp": exp,
        "tokenExp": exp,
    }
    return jwt.encode(payload, cfg.ZOOM_SDK_CLIENT_SECRET, algorithm="HS256")

def parse_zoom_url(url: str) -> tuple[str, str]:
    """Extract (meeting_number, passcode) from a Zoom URL."""
    match = re.match(
        r"https?://(?:[a-z0-9-]+\.)?zoom\.us/j/(\d+)(?:\?pwd=([a-zA-Z0-9]+))?",
        url, re.IGNORECASE
    )
    if not match:
        raise ValueError(f"Cannot extract meeting number from Zoom URL: {url}")
    return match.group(1), match.group(2) or ""
```

---

### Phase 2: Frontend – Zoom SDK Integration Page

**Files to modify/create:**

| Action   | File                                             | Description                                    |
|----------|--------------------------------------------------|------------------------------------------------|
| MODIFY   | `frontend/package.json`                          | Add `@zoom/meetingsdk` dependency              |
| NEW      | `frontend/src/app/zoom-meeting/page.tsx`         | Zoom Meeting SDK page component                |
| NEW      | `frontend/src/lib/zoom.ts`                       | Zoom SDK helper (init, join, event listeners)  |
| MODIFY   | `frontend/src/app/page.tsx`                      | Update dashboard to route Zoom links to SDK page |

**Key implementation:**

```typescript
// frontend/src/lib/zoom.ts

export async function getZoomSignature(meetingNumber: string, role: number = 0) {
  const res = await fetch(`${API_BASE}/api/zoom/signature`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ meeting_number: meetingNumber, role }),
  });
  const data = await res.json();
  return data.signature;
}

export function parseZoomUrl(url: string): { meetingNumber: string; passcode: string } {
  const match = url.match(/zoom\.us\/j\/(\d+)(?:\?pwd=([a-zA-Z0-9]+))?/i);
  if (!match) throw new Error('Invalid Zoom URL');
  return { meetingNumber: match[1], passcode: match[2] || '' };
}
```

---

### Phase 3: Pipeline Orchestrator Integration

**Files to modify:**

| Action   | File                              | Description                                         |
|----------|-----------------------------------|-----------------------------------------------------|
| MODIFY   | `backend/src/orchestrator.py`     | Add Zoom SDK routing logic for `_join_zoom` branch  |
| MODIFY   | `backend/modules/meeting_access.py` | Add `is_zoom_sdk_available()` check method        |

**Logic change in orchestrator:**
- For Zoom URLs: Skip `MeetingAccess.join()` for the joining stage. Instead, update meeting status to `JOINING`, then wait for the frontend SDK to signal a successful join via a webhook/API call.
- The OBS recording, transcription, summarisation, and delivery stages remain unchanged.

---

### Phase 4: Configuration & Testing

**Files to modify/create:**

| Action   | File                                  | Description                              |
|----------|---------------------------------------|------------------------------------------|
| MODIFY   | `backend/config/selectors.json`       | Keep Zoom selectors as fallback reference |
| NEW      | `frontend/tests/zoom-meeting.test.ts` | Frontend unit tests for Zoom SDK helpers |
| NEW      | `backend/tests/unit/test_zoom_route.py` | API endpoint integration tests         |

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zoom meetings join successfully via the SDK at a >95% rate (up from ~60-70% with Selenium).
- **SC-002**: The JWT signature endpoint responds in <100ms.
- **SC-003**: Meeting-end detection via SDK events triggers post-processing within 5 seconds (down from 30+ seconds with DOM polling).
- **SC-004**: All existing Google Meet and MS Teams flows continue working unchanged (zero regression).
- **SC-005**: The system gracefully falls back to Selenium for Zoom if SDK credentials are absent, with a warning log.
- **SC-006**: `ZOOM_SDK_CLIENT_SECRET` never appears in frontend bundle, API responses, or browser network traffic.

---

## Clarifications Needed

1. **Zoom Marketplace Account**: Does the team have access to a Zoom Developer account (Owner/Admin role) to create the Meeting SDK App on marketplace.zoom.us?
2. **Meeting SDK App Approval**: Meeting SDK Apps may require Zoom review for production use. Is the team aware of this approval process?
3. **Audio Capture Strategy**: The current plan keeps OBS for audio recording. Should we explore Zoom Cloud Recording API as a future alternative (requires additional Zoom API scopes)?
4. **Frontend Hosting**: The Zoom Meeting SDK renders inside a browser page. Will the AI Summarizer's frontend be accessible at a URL where the SDK can render (it cannot run headless)?
5. **Concurrent Meetings**: If multiple Zoom meetings run concurrently, each needs its own browser tab with the SDK. How many concurrent Zoom meetings should we support?
