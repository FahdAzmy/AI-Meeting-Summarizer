# Implementation Plan: Zoom Meeting SDK Integration

**Branch**: `011-zoom-meeting-sdk` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-zoom-meeting-sdk/spec.md`

## Summary

Replace the fragile browser-automation approach for Zoom meetings with the official Zoom Meeting SDK Web to join meetings programmatically. The backend will generate JWT signatures using `PyJWT`, the frontend will use the SDK to join meetings in a background page, and the pipeline orchestrator will route Zoom URLs through this new SDK path while preserving browser-automation for Google Meet and Teams.

## Technical Context

**Language/Version**: Python 3.10+ (backend), TypeScript/Next.js (frontend)
**Primary Dependencies**: `PyJWT>=2.8.0` (backend), `@zoom/meetingsdk` (frontend)
**Storage**: MongoDB (Beanie ODM) — no new collections needed
**Testing**: `pytest` (backend), Jest/Testing Library (frontend)
**Target Platform**: Web browser (background tab for meeting rendering) + FastAPI backend
**Project Type**: Full-stack web application
**Performance Goals**: Generate Zoom SDK tokens in <100ms; background SDK page loads and joins meeting in <15s
**Constraints**: SDK cannot run headlessly, requires a real browser tab. Audio capture still depends on OBS.
**Scale/Scope**: Support at least 3 concurrent Zoom meetings via isolated browser sessions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Test-Driven Development (TDD)**: The plan requires unit tests for the JWT generation, URL parsing, and the API endpoint before implementing the core orchestrator changes.
2. **High-Quality UI/UX Design**: The Zoom SDK meeting page will be hidden in the background, ensuring a clean dashboard experience where users just see status indicators updating dynamically. Error messages will be user-friendly.
3. **Async Processing & Performance Optimization**: The Zoom SDK page runs in a separate browser tab asynchronously, allowing the FastApi orchestrator to track the meeting without blocking.
4. **Modular & Extensible Architecture**: The Zoom SDK integration is encapsulated within a new `zoom_sdk` helper and router, ensuring the orchestrator simply uses the new path conditionally.
5. **Robust Observability & Error Handling**: Comprehensive logging for SDK events (join, end, waiting room timeout) will be added. Graceful fallback to the old Selenium approach is built-in if credentials are missing.

*Status: PASS*

## Project Structure

### Documentation (this feature)

```text
specs/011-zoom-meeting-sdk/
├── plan.md              # This file
├── research.md          # Technical analysis of SDK options
├── data-model.md        # Data models and interfaces
├── quickstart.md        # Quickstart for developers
├── contracts/           # API contracts
│   └── zoom_api.md
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
backend/
├── config/
│   └── settings.py
├── src/
│   ├── helpers/
│   │   └── zoom_sdk.py
│   ├── routes/
│   │   └── zoom.py
│   ├── main.py
│   └── orchestrator.py
├── requirements.txt
├── .env
├── .env.example
└── tests/
    └── unit/
        ├── test_zoom_sdk.py
        └── test_zoom_route.py

frontend/
├── package.json
├── src/
│   ├── app/
│   │   └── zoom-meeting/
│   │       └── page.tsx
│   └── lib/
│       └── zoom.ts
└── tests/
    └── zoom.test.ts
```

**Structure Decision**: The project uses a standard Next.js frontend + FastAPI backend structure. We will add a new helper module and route to the backend for Zoom JWT generation, and a new hidden Next.js page in the frontend to host the Zoom SDK.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | | |
