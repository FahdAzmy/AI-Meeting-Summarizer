---
description: "Task list for Frontend Dashboard feature implementation"
---

# Tasks: Frontend Dashboard

**Input**: Design documents from `/specs/002-frontend-dashboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md

**Tests**: Test-Driven Development (TDD) is explicitly enforced in this project's constitution. Test tasks are listed before implementation tasks and MUST be written to fail before being implemented.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [ ] T001 Initialize Next.js 14+ (App Router) project with TypeScript and Tailwind CSS in `frontend/`
- [ ] T002 Configure ESLint, Prettier, and basic linting rules in `frontend/`
- [ ] T003 Configure Jest and React Testing Library in `frontend/jest.config.js`
- [ ] T004 Configure Playwright for E2E testing in `frontend/playwright.config.ts`
- [ ] T005 Create `.env.local` template with `NEXT_PUBLIC_API_URL` based on `quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Write base TypeScript interfaces (`Meeting`, `ActionItem`, `Settings`, `PipelineStatus`) in `frontend/src/lib/types.ts`
- [ ] T007 [P] Create API Client Wrapper (`api.ts`) mocking all backend calls detailed in `api-contracts.md` in `frontend/src/lib/api.ts`
- [ ] T008 [P] Implement core UI Layout (Navbar, Sidebar) in `frontend/src/app/layout.tsx`
- [ ] T009 Create reusable UI primitive components (Input, Button, Toast) in `frontend/src/components/ui/` using Tailwind CSS
- [ ] T010 Setup global error boundaries so failed API calls surface non-technical errors to users.

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Join a Meeting via Dashboard (Priority: P1) 🎯 MVP

**Goal**: Users need a central entry point where they can submit a virtual meeting link along with the participants' email addresses to initiate the AI assistant pipeline.

**Independent Test**: Can be tested by filling out the dashboard form, clicking "Join Meeting", verifying the request is sent, and observing the real-time polling state.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for URL platform verification and regex parsing in `frontend/tests/unit/utils.test.ts`
- [ ] T012 [P] [US1] Integration tests for `MeetingForm` UI validation rendering in `frontend/tests/unit/components/MeetingForm.test.tsx`
- [ ] T013 [P] [US1] Playwright E2E test for full dashboard join flow and polling observation in `frontend/tests/e2e/dashboardFlow.spec.ts`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Create `PlatformBadge` component to render detected platform in `frontend/src/components/dashboard/PlatformBadge.tsx`
- [ ] T015 [P] [US1] Create `StatusPanel` component to poll `/api/status/:session_id` every 3 seconds in `frontend/src/components/dashboard/StatusPanel.tsx`
- [ ] T016 [US1] Create `MeetingForm` component with Client-side validation in `frontend/src/components/dashboard/MeetingForm.tsx` (Depends on T014)
- [ ] T017 [US1] Implement Main Dashboard Page combining `MeetingForm` and `StatusPanel` in `frontend/src/app/page.tsx`
- [ ] T018 [US1] Implement success transition on status "completed" to show toast and navigation prompt in `frontend/src/app/page.tsx`

**Checkpoint**: At this point, the core meeting submission flow and polling are fully functional independently.

---

## Phase 4: User Story 2 - Browse Meeting History (Priority: P2)

**Goal**: Users need to see a chronological list of their past AI-processed meetings.

**Independent Test**: Can be verified by viewing the table populated via the mock API and verifying sorting behaviors on the client side.

### Tests for User Story 2  ⚠️

- [ ] T019 [P] [US2] Component test for `MeetingsTable` ensuring proper sorting algorithms in `frontend/tests/unit/components/MeetingsTable.test.tsx`
- [ ] T020 [P] [US2] Playwright E2E test for history view loading properly within 2 seconds limit in `frontend/tests/e2e/historyFlow.spec.ts`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Create color-coded `StatusBadge` Component in `frontend/src/components/history/StatusBadge.tsx`
- [ ] T022 [P] [US2] Create `MeetingRow` Component for table layout in `frontend/src/components/history/MeetingRow.tsx`
- [ ] T023 [US2] Create `MeetingsTable` Component implementing client-side sorting by Date, Platform, Duration, Status in `frontend/src/components/history/MeetingsTable.tsx`
- [ ] T024 [US2] Implement History Page calling `api.getMeetings()` on load in `frontend/src/app/history/page.tsx`

**Checkpoint**: Users can now list and sort all executed meetings flawlessly.

---

## Phase 5: User Story 3 - View Detailed Meeting Analysis (Priority: P3)

**Goal**: Users need to deeply explore the outputs of a completed meeting, including the full text summary, decisions, task assignments, and verbatim transcript.

**Independent Test**: Load the detail page route corresponding to an ID and verify all child components parse the API JSON properly.

### Tests for User Story 3  ⚠️

- [ ] T025 [P] [US3] Component tests for various sub-sections parsing mock Meeting objects correctly in `frontend/tests/unit/components/DetailSections.test.tsx`
- [ ] T026 [P] [US3] Playwright E2E test accessing a specific meeting detail page and checking 404 paths in `frontend/tests/e2e/detailFlow.spec.ts`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Create `SummarySection` component to map markdown blocks in `frontend/src/components/detail/SummarySection.tsx`
- [ ] T028 [P] [US3] Create `ActionItemsTable` and `DecisionsList` components for structured data in `frontend/src/components/detail/ActionItemsTable.tsx`
- [ ] T029 [P] [US3] Create collapsible `TranscriptViewer` component in `frontend/src/components/detail/TranscriptViewer.tsx`
- [ ] T030 [P] [US3] Create `SpeakerStats` component to ingest and render diarization facts in `frontend/src/components/detail/SpeakerStats.tsx`
- [ ] T031 [US3] Implement Detailed View Page parsing from `api.getMeeting(id)` combining all segments in `frontend/src/app/history/[id]/page.tsx`
- [ ] T032 [US3] Implement 404 fallback page logic for non-existent meeting IDs in `frontend/src/app/history/[id]/not-found.tsx`

**Checkpoint**: Detail page renders complete output objects correctly.

---

## Phase 6: User Story 4 - System Settings Configuration (Priority: P4)

**Goal**: Users need to configure global preferences that govern how the backend pipeline behaves.

**Independent Test**: Update and save settings in the form. Validate it sends the correct API payload to the backend.

### Tests for User Story 4  ⚠️

- [ ] T033 [P] [US4] Component test for form validation and API state saving in `frontend/tests/unit/components/Settings.test.tsx`

### Implementation for User Story 4

- [ ] T034 [P] [US4] Create `StorageToggle` UI component handling database vs google_sheets in `frontend/src/components/settings/StorageToggle.tsx`
- [ ] T035 [P] [US4] Create `STTSelector` and `EmailConfig` components in `frontend/src/components/settings/STTSelector.tsx`
- [ ] T036 [US4] Implement Settings Page to fetch active configs and post updates in `frontend/src/app/settings/page.tsx`

**Checkpoint**: Global configurations persist through UI adjustments.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T037 Check responsiveness across all screens validating formatting on 375px mobile breakpoint.
- [ ] T038 Review all API call hooks for proper non-technical error notifications (Toasts).
- [ ] T039 Execute combined test suite ensuring everything passes reliably.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel if multiple engineers are staffed.
  - Or sequentially in priority order (US1 → US2 → US3 → US4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Parallel Opportunities

- All Foundational tasks (T006 - T008) can run concurrently.
- All Component testing tasks for each User Story can run alongside their corresponding Component build tasks (T011 alongside T014, etc.)
- User Stories 2, 3, and 4 are structurally independent of each other (once `api.ts` foundation is in).

### Implementation Strategy

#### MVP First (User Story 1 Only)
1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Tests then components)
4. **STOP and VALIDATE**: Test User Story 1 independently end to end.
5. Deploy/demo if ready.
