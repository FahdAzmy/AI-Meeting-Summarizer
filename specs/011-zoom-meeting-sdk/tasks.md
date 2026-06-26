---
description: "Task list for Zoom Meeting SDK Integration"
---

# Tasks: Zoom Meeting SDK Integration

**Input**: Design documents from `/specs/011-zoom-meeting-sdk/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Add `PyJWT>=2.8.0` dependency to `backend/requirements.txt`
- [X] T002 [P] Install `@zoom/meetingsdk` dependency in `frontend/package.json`
- [X] T003 Update configuration schema in `backend/config/settings.py` for `ZOOM_SDK_CLIENT_ID` and `ZOOM_SDK_CLIENT_SECRET`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `backend/src/helpers/zoom_sdk.py` placeholder module
- [X] T005 Setup `backend/src/routes/zoom.py` placeholder module

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 3 - Zoom Meeting Link Parsing (Priority: P1) 🎯 MVP

**Goal**: Extract the meeting identifier and optional passcode from any valid Zoom URL.

**Independent Test**: Can be tested independently with a suite of different Zoom URL formats.

### Tests for User Story 3

- [X] T006 [P] [US3] Create tests for URL parsing in `backend/tests/unit/test_zoom_sdk.py`

### Implementation for User Story 3

- [X] T007 [US3] Implement URL parsing regex logic in `backend/src/helpers/zoom_sdk.py`

**Checkpoint**: URL parsing works independently

---

## Phase 4: User Story 5 - Secure Credential Management (Priority: P2)

**Goal**: Expose a secure, public endpoint that returns a time-limited authorisation token for the Zoom SDK.

**Independent Test**: Inspect API responses to verify the secret is never transmitted.

### Tests for User Story 5

- [X] T008 [P] [US5] Create tests for JWT signature generation in `backend/tests/unit/test_zoom_route.py`

### Implementation for User Story 5

- [X] T009 [US5] Implement JWT token generation using `PyJWT` in `backend/src/helpers/zoom_sdk.py`
- [X] T010 [US5] Implement `POST /api/zoom/signature` endpoint in `backend/src/routes/zoom.py`
- [X] T011 [US5] Include `zoom` router in `backend/src/main.py`

**Checkpoint**: Authorisation token endpoint works independently

---

## Phase 5: User Story 1 - Reliable Zoom Meeting Join (Priority: P1)

**Goal**: Join Zoom meetings reliably using the official SDK instead of scraping the UI.

**Independent Test**: Provide a valid Zoom meeting link and verify the system automatically joins as "AI Summarizer".

### Tests for User Story 1

- [X] T012 [P] [US1] Create frontend tests for Zoom wrapper in `frontend/tests/zoom.test.ts`

### Implementation for User Story 1

- [X] T013 [US1] Create Zoom SDK initialization wrapper in `frontend/src/lib/zoom.ts`
- [X] T014 [US1] Implement dedicated background meeting page in `frontend/src/app/zoom-meeting/page.tsx`

**Checkpoint**: The background page can join a meeting using the SDK

---

## Phase 6: User Story 2 - Native Meeting End Detection (Priority: P1)

**Goal**: Use native event-driven callbacks to instantly detect when the meeting ends.

**Independent Test**: Join a meeting, end it, and verify the system detects the end event within 5 seconds.

### Implementation for User Story 2

- [X] T015 [US2] Add event listeners (e.g. `onLeave`) to the SDK client in `frontend/src/app/zoom-meeting/page.tsx`
- [X] T016 [US2] Implement backend API call from frontend to update pipeline status when meeting ends

**Checkpoint**: The frontend can detect meeting end and update the backend

---

## Phase 7: User Story 4 - Multi-Platform Coexistence (Priority: P2)

**Goal**: Route Zoom links through the SDK path, while maintaining Selenium support for other platforms and fallback.

**Independent Test**: Submit links for Zoom, Google Meet, and Teams, and verify correct routing.

### Implementation for User Story 4

- [X] T017 [US4] Update `backend/src/orchestrator.py` to route Zoom URLs to the new SDK background page
- [X] T018 [US4] Implement fallback to Selenium in `orchestrator.py` if `ZOOM_SDK_CLIENT_SECRET` is missing

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T019 Run `quickstart.md` validation by testing the generated token endpoint
- [X] T020 Code cleanup and final formatting checks

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Stories (Phase 3-7)**: Depend on Foundational phase. Best executed sequentially to build upon each other (URL parsing -> Credentials -> Join -> End Detection -> Routing).
- **Polish (Phase 8)**: Depends on all user stories being complete.

### User Story Dependencies

- **US3 (Parsing)**: Independent
- **US5 (Credentials)**: Independent, but required before US1.
- **US1 (Join)**: Depends on US3 and US5.
- **US2 (End Detection)**: Depends on US1.
- **US4 (Orchestration)**: Depends on all other stories to fully test routing.

### Parallel Opportunities

- T001 and T002 can be executed in parallel.
- US3 and US5 can technically be implemented in parallel by different backend engineers.
- US1 frontend implementation can start in parallel with backend tasks, mocking the API response.

---

## Implementation Strategy

### Incremental Delivery

1. Complete Setup & Foundation.
2. Complete US3 (URL Parsing) and US5 (Token API). This establishes the backend API.
3. Complete US1 (Join). This establishes the frontend SDK UI.
4. Complete US2 (End Detection) to make the UI fully functional for the pipeline.
5. Complete US4 (Orchestrator Integration) to wire the pipeline together.
