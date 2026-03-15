# Implementation Plan: Frontend Dashboard

**Branch**: `002-frontend-dashboard` | **Date**: 2026-03-15 | **Spec**: [specs/002-frontend-dashboard/spec.md](spec.md)
**Input**: Feature specification from `/specs/002-frontend-dashboard/spec.md`

## Summary

The Frontend Dashboard provides the user interface for the AI Meeting Assistant. It acts as the central entry point for users to submit meeting links, view a chronological history of past meetings, deeply explore generated summaries and transcripts, and configure global application preferences. This dashboard calls the Python FastAPI backend via HTTP endpoints.

## Technical Context

**Language/Version**: TypeScript, React 18, Node.js 18+
**Primary Dependencies**: Next.js 14+ (App Router), Tailwind CSS, React Hook Form (for forms)
**Storage**: N/A (Frontend only maintains local/session UI state; data rests in backend DB/Sheets via Python API)
**Testing**: Jest + React Testing Library (Unit/Integration), Playwright (E2E)
**Target Platform**: Web Browsers (Chrome, Edge, Safari, Firefox)
**Project Type**: web-service (frontend web application)
**Performance Goals**: Dashboard historical table rendering under 2 seconds for 100+ records; minimal rendering lag during real-time polling updates.
**Constraints**: 3-second maximum visual latency when polling status endpoints; responsive at minimum width of 375px.
**Scale/Scope**: Designed to handle primarily individual user scopes or small team access to the AI Pipeline backend.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Test-Driven Development**: `plan.md` specifies TDD tools (Jest/RTL). Tests must be written before implementation.
- [x] **II. High-Quality UI/UX Design**: Uses Tailwind for modern styling, specifies polling UI state (no blocking).
- [x] **III. Async Processing & Performance Optimization**: Relies on asynchronous client-side API calls to prevent blocking the UI.
- [x] **IV. Modular & Extensible Architecture**: Frontend cleanly separated from Python backend via REST interface contracts.
- [x] **V. Robust Observability & Error Handling**: Non-technical error states provided for 100% of API fail cases.

*Status: PASS*

## Project Structure

### Documentation (this feature)

```text
specs/002-frontend-dashboard/
├── plan.md              # This file
├── research.md          # Technical analysis and architecture decisions
├── data-model.md        # Entities involved on the frontend side
├── quickstart.md        # Feature-specific bootup instructions
├── contracts/           # Interface contracts between frontend and backend
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx         # Shared root layout
│   │   ├── page.tsx           # Dashboard / Join Form
│   │   ├── history/
│   │   │   ├── page.tsx       # Meeting History
│   │   │   └── [id]/page.tsx  # Detailed Meeting View
│   │   └── settings/
│   │       └── page.tsx       # System Settings
│   ├── components/
│   │   ├── ui/                # Base reusable components (Buttons, Input, Badges)
│   │   └── features/          # Feature-level grouped components
│   └── lib/
│       ├── api.ts             # API Client Wrapper
│       └── types.ts           # Typescript interfaces corresponding to data-model and contracts
└── tests/
    ├── e2e/                   # Playwright E2E specs
    └── unit/                  # Jest / React Testing Library unit specs
```

**Structure Decision**: The project uses **Option 2: Web application** separated as `frontend/` leveraging the Next.js App Router structure under `src/app`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None*    | *N/A*      | *N/A*                               |
