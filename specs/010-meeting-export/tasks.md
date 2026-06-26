---
description: "Task list for Meeting Export (Excel & PDF)"
---

# Tasks: Meeting Export (Excel & PDF)

**Input**: Design documents from `/specs/010-meeting-export/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.
**Methodology**: Strictly following TDD (Tests written before implementation) as per the project Constitution.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths are included in all descriptions.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Add `openpyxl` and `reportlab` to `backend/requirements.txt`
- [X] T002 Create empty `backend/src/routes/export.py` and wire it into the main router in `backend/src/routes/api.py`

---

## Phase 2: Foundational & User Story 4 - Remove Google Sheets Export (Priority: P1)

**Goal**: The existing Google Sheets integration for saving meeting data is removed from the system. This provides a clean baseline.

**Independent Test**: The system functions and tests pass without any Google API credentials configured.

### Tests Update for User Story 4 ⚠️
> **NOTE: Write/Update these tests FIRST**

- [X] T003 [US4] Remove Google Sheets test cases and mock data from `backend/tests/unit/test_output_storage.py`

### Implementation for User Story 4

- [X] T004 [US4] Remove `_store_to_sheets`, `_write_csv_fallback`, and `gspread`/`pandas` imports from `backend/modules/output_storage.py`
- [X] T005 [P] [US4] Remove `SheetsWriteError` and `google_sheets` from `VALID_BACKENDS` in `backend/modules/storage_errors.py`
- [X] T006 [P] [US4] Remove `GOOGLE_SHEETS_ID` and `GOOGLE_CREDENTIALS_PATH` config fields from `backend/config/settings.py`
- [X] T007 [P] [US4] Remove `sheets` backend mapping from `backend/src/orchestrator.py`
- [X] T008 [P] [US4] Remove `gspread` dependency from `backend/requirements.txt`
- [X] T009 [P] [US4] Remove `google_sheets` storage option from `frontend/src/components/settings/StorageToggle.tsx` and `frontend/src/lib/types.ts`

**Checkpoint**: Foundation ready - Google Sheets logic is fully removed and tests pass.

---

## Phase 3: User Story 1 - Export All Meetings as Excel (Priority: P1) 🎯 MVP

**Goal**: A bulk data export endpoint and UI button generating an Excel file containing all completed meetings.

**Independent Test**: Clicking the export button on the History page downloads an Excel file with all completed meetings.cc

### Tests for User Story 1 ⚠️
> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Create Excel generator tests in `backend/tests/unit/test_excel_generator.py`
- [X] T011 [P] [US1] Create export-all endpoint integration tests in `backend/tests/unit/test_export.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `generate_all_meetings_excel` function in `backend/src/helpers/excel_generator.py`
- [X] T013 [US1] Implement `GET /api/export/meetings/excel` endpoint in `backend/src/routes/export.py`
- [X] T014 [P] [US1] Add `exportAllMeetingsExcel` API client method in `frontend/src/lib/api.ts`
- [X] T015 [US1] Add "Export All Meetings" button with loading state in `frontend/src/app/history/page.tsx`

**Checkpoint**: User Story 1 (Bulk Excel) should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Export Single Meeting as PDF (Priority: P1)

**Goal**: Generate a professional, print-ready structured PDF document for a single meeting.

**Independent Test**: Clicking "Export as PDF" on the detail page downloads a structured PDF with all meeting data.

### Tests for User Story 2 ⚠️

- [X] T016 [P] [US2] Create PDF generator unit tests in `backend/tests/unit/test_pdf_generator.py`
- [X] T017 [P] [US2] Create export-pdf endpoint integration tests in `backend/tests/unit/test_export.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `generate_meeting_pdf` function in `backend/src/helpers/pdf_generator.py`
- [X] T019 [US2] Implement `GET /api/export/meetings/{id}/pdf` endpoint in `backend/src/routes/export.py`
- [X] T020 [P] [US2] Add `exportMeetingPdf` API client method in `frontend/src/lib/api.ts`
- [X] T021 [US2] Add "Export as PDF" button in `frontend/src/app/history/[id]/page.tsx`

**Checkpoint**: User Story 2 (Single PDF) should be independently functional.

---

## Phase 5: User Story 3 - Export Single Meeting as Excel (Priority: P2)

**Goal**: Export an individual meeting's data in a spreadsheet format.

**Independent Test**: Clicking "Export as Excel" on the detail page downloads an Excel file for that specific meeting.

### Tests for User Story 3 ⚠️

- [X] T022 [P] [US3] Add single meeting generation tests to `backend/tests/unit/test_excel_generator.py`
- [X] T023 [P] [US3] Add export-single-excel endpoint tests to `backend/tests/unit/test_export.py`

### Implementation for User Story 3

- [X] T024 [US3] Implement `generate_single_meeting_excel` function in `backend/src/helpers/excel_generator.py`
- [X] T025 [US3] Implement `GET /api/export/meetings/{id}/excel` endpoint in `backend/src/routes/export.py`
- [X] T026 [P] [US3] Add `exportMeetingExcel` API client method in `frontend/src/lib/api.ts`
- [X] T027 [US3] Add "Export as Excel" button in `frontend/src/app/history/[id]/page.tsx`

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T028 [P] Run `grep -r "google_sheets" backend/ frontend/` to ensure 100% removal
- [X] T029 Perform manual E2E validation against the requirements in `quickstart.md`
- [X] T030 Ensure unified loading and error handling toast messages across frontend export buttons

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Start immediately
- **Foundational (Phase 2, US4)**: Must be completed first to clean up the backend storage layer.
- **User Stories (Phase 3-5)**: Depend on Phase 1 & 2. US1, US2, US3 can technically be done in parallel, but prioritizing them sequentially (P1 -> P1 -> P2) is recommended.
- **Polish (Phase N)**: Follows the completion of all user stories.

### User Story Dependencies

- **User Story 4 (P1 - Foundational)**: Modifies existing storage modules. No dependencies.
- **User Story 1 (P1)**: Generates Excel. Relies on the `export.py` router from Phase 1.
- **User Story 2 (P1)**: Generates PDF. Independent from US1.
- **User Story 3 (P2)**: Generates Excel. Expands on the generator file created in US1.

### Parallel Opportunities

- Tests within the same user story can be written concurrently.
- Frontend API client additions (`api.ts`) can be done concurrently with backend endpoint implementations.
- US2 (PDF) can be implemented in parallel with US1 (Excel) if multiple developers are assigned.

---

## Parallel Example: User Story 1

```bash
# Developer A starts backend TDD
Task: "T010 [US1] Create Excel generator tests in backend/tests/unit/test_excel_generator.py"
Task: "T011 [US1] Create export-all endpoint integration tests in backend/tests/unit/test_export.py"

# Developer B sets up the frontend API client
Task: "T014 [US1] Add exportAllMeetingsExcel API client method in frontend/src/lib/api.ts"
```

## Implementation Strategy

### MVP First (User Story 4 + User Story 1)

1. **Phase 1**: Add dependencies & basic router.
2. **Phase 2 (US4)**: Strip out Google Sheets code to clean up the architecture.
3. **Phase 3 (US1)**: Implement Excel bulk export.
4. **Validate**: Verify Google Sheets is gone and Bulk Excel download works perfectly.

### Incremental Delivery

1. Setup + US4 → Clean codebase
2. Add US1 → Test independently → Excel Bulk Export MVP
3. Add US2 → Test independently → Single PDF Export Added
4. Add US3 → Test independently → Single Excel Export Added
