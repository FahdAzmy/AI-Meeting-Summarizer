# Implementation Plan: Zoom Meeting SDK Integration

**Branch**: `011-zoom-meeting-sdk` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/011-zoom-meeting-sdk/spec.md`

## Summary

Replace the fragile Selenium-based Zoom join flow with the official Zoom Meeting SDK for Web (`@zoom/meetingsdk`). The backend generates JWT signatures using `PyJWT`, the frontend uses the SDK to join meetings programmatically, and the pipeline orchestrator is updated to route Zoom meetings through the SDK path while preserving Selenium for Google Meet and MS Teams.

## Technical Context

**Language/Version**: Python 3.10+ (backend), TypeScript/Next.js 16 (frontend)  
**Primary Dependencies**:
- Backend: `PyJWT>=2.8.0` (JWT signature generation)
- Frontend: `@zoom/meetingsdk` (Zoom Web SDK)  

**Storage**: MongoDB (Beanie ODM) — no schema changes required  
**Testing**: `pytest` (backend), Jest (frontend), manual E2E verification  
**Target Platform**: Chrome browser (non-headless) for SDK rendering + OBS for audio capture  
**Project Type**: Full-stack feature (backend API + frontend page + orchestrator update)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Test-Driven Development**: Unit tests for JWT generation, URL parsing, and API endpoints written before implementation.
- [x] **II. High-Quality UI/UX Design**: The SDK renders the standard Zoom meeting UI — no custom UI needed.
- [x] **III. Async Processing & Performance Optimization**: JWT generation is synchronous but <1ms. SDK loading is async on the frontend page only.
- [x] **IV. Modular & Extensible Architecture**: New `zoom_sdk.py` helper is isolated; orchestrator routing is config-driven; Selenium fallback preserved.
- [x] **V. Robust Observability & Error Handling**: Structured logging for join/end events; graceful fallback on SDK failure; secrets never exposed.

*Status: PASS*

## Project Structure

### Documentation (this feature)

```text
specs/011-zoom-meeting-sdk/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Technical analysis of SDK options
└── tasks.md             # Implementation tasks (to be created)
```

### Source Code Changes

```text
backend/
├── config/
│   └── settings.py                     # [MODIFY] Add ZOOM_SDK_* env vars
├── src/
│   ├── helpers/
│   │   └── zoom_sdk.py                 # [NEW] generate_signature() + parse_zoom_url()
│   ├── routes/
│   │   └── zoom.py                     # [NEW] POST /api/zoom/signature
│   ├── main.py                         # [MODIFY] Register Zoom router
│   └── orchestrator.py                 # [MODIFY] Add Zoom SDK routing logic
├── requirements.txt                    # [MODIFY] Add pyjwt>=2.8.0
├── .env                                # [MODIFY] Add ZOOM_SDK_CLIENT_ID/SECRET
├── .env.example                        # [MODIFY] Add placeholder entries
└── tests/
    └── unit/
        ├── test_zoom_sdk.py            # [NEW] Tests for helpers
        └── test_zoom_route.py          # [NEW] Tests for API endpoint

frontend/
├── package.json                        # [MODIFY] Add @zoom/meetingsdk
├── src/
│   ├── app/
│   │   └── zoom-meeting/
│   │       └── page.tsx                # [NEW] Zoom SDK meeting page
│   └── lib/
│       └── zoom.ts                     # [NEW] SDK helpers (init, join, events)
└── tests/
    └── zoom.test.ts                    # [NEW] Frontend unit tests
```

## Implementation Phases

### Phase 1: Backend Infrastructure (JWT + URL Parsing)

**Goal**: Create the backend foundation — secure JWT generation and Zoom URL parsing.

#### 1.1 Add Zoom SDK Config Fields

**File**: `backend/config/settings.py`
- Add `ZOOM_SDK_CLIENT_ID: str = Field(default="", description="...")`
- Add `ZOOM_SDK_CLIENT_SECRET: str = Field(default="", description="...")`

**File**: `backend/.env.example`
- Add `ZOOM_SDK_CLIENT_ID=` and `ZOOM_SDK_CLIENT_SECRET=` placeholders

#### 1.2 Create Zoom SDK Helper Module

**File**: `backend/src/helpers/zoom_sdk.py` [NEW]

```python
"""Zoom Meeting SDK helper functions."""
import re
import time
import jwt
from config.settings import Config

_ZOOM_URL_PATTERN = re.compile(
    r"https?://(?:[a-z0-9-]+\.)?zoom\.us/j/(\d+)(?:\?pwd=([a-zA-Z0-9]+))?",
    re.IGNORECASE,
)

def generate_signature(meeting_number: str, role: int = 0) -> str:
    cfg = Config()
    if not cfg.ZOOM_SDK_CLIENT_ID or not cfg.ZOOM_SDK_CLIENT_SECRET:
        raise ValueError("ZOOM_SDK_CLIENT_ID and ZOOM_SDK_CLIENT_SECRET must be set")
    iat = int(time.time())
    exp = iat + 7200
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
    match = _ZOOM_URL_PATTERN.match(url)
    if not match:
        raise ValueError(f"Cannot extract meeting number from: {url}")
    return match.group(1), match.group(2) or ""

def is_zoom_sdk_configured() -> bool:
    cfg = Config()
    return bool(cfg.ZOOM_SDK_CLIENT_ID and cfg.ZOOM_SDK_CLIENT_SECRET)
```

#### 1.3 Create Zoom Signature API Route

**File**: `backend/src/routes/zoom.py` [NEW]

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.helpers.zoom_sdk import generate_signature, is_zoom_sdk_configured

router = APIRouter(prefix="/api/zoom", tags=["zoom"])

class SignatureRequest(BaseModel):
    meeting_number: str
    role: int = 0

class SignatureResponse(BaseModel):
    signature: str
    sdk_key: str

@router.post("/signature", response_model=SignatureResponse)
async def create_signature(req: SignatureRequest):
    if not is_zoom_sdk_configured():
        raise HTTPException(503, "Zoom SDK credentials not configured")
    sig = generate_signature(req.meeting_number, req.role)
    from config.settings import Config
    return SignatureResponse(signature=sig, sdk_key=Config().ZOOM_SDK_CLIENT_ID)
```

#### 1.4 Register Router + Add Dependency

**File**: `backend/src/main.py` — add `from src.routes.zoom import router as zoom_router` and `app.include_router(zoom_router)`.

**File**: `backend/requirements.txt` — add `pyjwt>=2.8.0`.

---

### Phase 2: Frontend SDK Integration

**Goal**: Create a Next.js page that loads the Zoom Meeting SDK and joins a meeting.

#### 2.1 Install SDK Package

```bash
cd frontend && npm install @zoom/meetingsdk --save
```

#### 2.2 Create Zoom Helper Library

**File**: `frontend/src/lib/zoom.ts` [NEW]

- `getZoomSignature(meetingNumber, role)` — calls backend API
- `parseZoomUrl(url)` — extracts meeting number + passcode
- `initAndJoinZoom(config)` — initializes SDK and joins meeting

#### 2.3 Create Zoom Meeting Page

**File**: `frontend/src/app/zoom-meeting/page.tsx` [NEW]

- Client-side page (`'use client'`) that:
  1. Reads `meetingNumber` and `passcode` from URL search params
  2. Calls backend for JWT signature
  3. Initializes `ZoomMtg` and calls `join()`
  4. Listens for meeting-end events
  5. Notifies backend when meeting ends → triggers pipeline

#### 2.4 Update Dashboard

**File**: `frontend/src/app/page.tsx` [MODIFY]

- When user submits a Zoom link, detect it and redirect to `/zoom-meeting?mn=...&pwd=...` instead of the generic pipeline start flow.

---

### Phase 3: Pipeline Orchestrator Update

**Goal**: Route Zoom meetings through the SDK path while preserving Selenium for other platforms.

#### 3.1 Modify Orchestrator Join Logic

**File**: `backend/src/orchestrator.py` [MODIFY]

The current flow:
```
JOINING → MeetingAccess.join(link) → RECORDING → ...
```

New flow for Zoom with SDK:
```
JOINING → (SDK join happens on frontend) → wait for join callback → RECORDING → ...
```

**Key change**: For Zoom URLs when SDK is configured, the orchestrator skips the `MeetingAccess.join()` call and instead waits for a frontend callback (via a new endpoint or polling the meeting status).

For non-Zoom URLs or when SDK is not configured, the existing Selenium flow remains unchanged.

---

### Phase 4: Testing & Verification

#### Unit Tests (Backend)
- `test_zoom_sdk.py`: Test `generate_signature()` produces valid JWT, `parse_zoom_url()` handles all URL formats, `is_zoom_sdk_configured()` returns correct boolean.
- `test_zoom_route.py`: Test `POST /api/zoom/signature` returns 200 with valid credentials, 503 without.

#### Unit Tests (Frontend)
- `zoom.test.ts`: Test `parseZoomUrl()` extraction logic, test `getZoomSignature()` API call mocking.

#### Manual E2E Verification
1. Create a test Zoom meeting
2. Submit the link through the dashboard
3. Verify the SDK page loads and joins the meeting
4. End the meeting and verify the pipeline triggers

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Frontend page for SDK | SDK requires DOM rendering | Cannot run headless; no simpler alternative exists |
| Two join paths (SDK + Selenium) | Multi-platform support | Dropping Selenium breaks Google Meet/Teams |
| JWT generation endpoint | SDK requires server-signed tokens | Client-side signing exposes secrets |
