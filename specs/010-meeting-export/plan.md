# Implementation Plan: Meeting Export (Excel & PDF)

**Branch**: `010-meeting-export` | **Date**: 2026-04-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-meeting-export/spec.md`

## Summary

Replace the Google Sheets export functionality with self-contained Excel and PDF export endpoints. The backend exposes three new REST endpoints that query completed meetings from MongoDB and generate downloadable `.xlsx` and `.pdf` files server-side using `openpyxl` and `reportlab`. The frontend adds export buttons to the History page (bulk Excel) and Meeting Detail page (single PDF + single Excel). All Google Sheets code, configuration, and dependencies are fully removed.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/Next.js 15 (frontend)  
**Primary Dependencies**: FastAPI, openpyxl (Excel), reportlab (PDF), Beanie ODM (MongoDB)  
**Storage**: MongoDB (existing `meetings` collection, read-only for this feature)  
**Testing**: pytest with AsyncMock (backend), Jest (frontend)  
**Target Platform**: Web application (desktop browser)  
**Project Type**: Web service (REST API + SPA frontend)  
**Performance Goals**: ≤10s for 200-meeting Excel export, ≤5s for single PDF, ≤3s for single Excel  
**Constraints**: LTR/English only, server-side generation with streaming response  
**Scale/Scope**: Up to 200 meetings per export, individual meeting transcripts up to 2 hours

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD | ✅ Pass | Tests for export generators and endpoints will be written before implementation |
| II. UI/UX Excellence | ✅ Pass | Export buttons follow existing design system (stone/emerald palette, rounded-xl, animations) |
| III. Async Processing | ✅ Pass | Export endpoints use async Beanie queries; file generation is CPU-bound but fast enough for sync within request |
| IV. Modular Architecture | ✅ Pass | Export logic isolated in `helpers/excel_generator.py` and `helpers/pdf_generator.py`, separate from existing `output_storage.py` |
| V. Observability | ✅ Pass | Structured logging for export requests, timing, and errors |

**Post-Design Re-check**: All gates still pass. No new dependencies introduce architectural violations. The export helpers are pure utility modules with no side effects beyond the returned file bytes.

## Project Structure

### Documentation (this feature)

```text
specs/010-meeting-export/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity mapping
├── quickstart.md        # Phase 1: dev setup guide
├── contracts/
│   └── api.md           # Phase 1: REST endpoint contracts
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── routes/
│   │   ├── api.py              # Existing (modify: remove sheets references)
│   │   └── export.py           # NEW: export endpoint router
│   ├── helpers/
│   │   ├── excel_generator.py  # NEW: openpyxl Excel generation
│   │   └── pdf_generator.py    # NEW: reportlab PDF generation
│   ├── models/
│   │   └── meeting.py          # Existing (no changes)
│   └── orchestrator.py         # Existing (modify: remove sheets mapping)
├── modules/
│   ├── output_storage.py       # Existing (modify: remove Sheets code)
│   └── storage_errors.py       # Existing (modify: remove SheetsWriteError)
├── config/
│   └── settings.py             # Existing (modify: remove Sheets config)
└── tests/
    └── unit/
        ├── test_export.py          # NEW: export endpoint tests
        ├── test_excel_generator.py  # NEW: Excel generation tests
        ├── test_pdf_generator.py    # NEW: PDF generation tests
        └── test_output_storage.py   # Existing (modify: remove Sheets tests)

frontend/
├── src/
│   ├── app/
│   │   └── history/
│   │       ├── page.tsx         # Existing (modify: add Export All button)
│   │       └── [id]/
│   │           └── page.tsx     # Existing (modify: add PDF + Excel buttons)
│   ├── lib/
│   │   ├── api.ts              # Existing (modify: add export methods)
│   │   └── types.ts            # Existing (modify: remove google_sheets)
│   └── components/
│       └── settings/
│           └── StorageToggle.tsx # Existing (modify: remove Sheets option)
└── tests/                       # Existing test structure
```

**Structure Decision**: Web application (Option 2) — matches the existing monorepo layout with `backend/` and `frontend/` directories. New export logic is placed in `backend/src/helpers/` (pure utility) and `backend/src/routes/export.py` (endpoint layer), keeping clean separation from the pipeline's `modules/output_storage.py`.

## Implementation Phases

### Phase 1: Google Sheets Removal (US-4, P1)

Remove all Google Sheets code, config, and dependencies. This is done first to create a clean baseline.

**Files to modify**:
- `backend/modules/output_storage.py` — Remove `_store_to_sheets()`, `_write_csv_fallback()`, `gspread`/`pandas` imports, Sheets config from `__init__`, `google_sheets` from `_VALID_BACKENDS`
- `backend/modules/storage_errors.py` — Remove `SheetsWriteError`, `google_sheets` from `VALID_BACKENDS`
- `backend/config/settings.py` — Remove `GOOGLE_SHEETS_ID`, `GOOGLE_CREDENTIALS_PATH`
- `backend/src/orchestrator.py` — Remove `sheets` mapping from `backend_map`
- `backend/tests/unit/test_output_storage.py` — Remove Google Sheets test cases
- `frontend/src/lib/types.ts` — Remove `google_sheets` from `StorageBackend`
- `frontend/src/components/settings/StorageToggle.tsx` — Remove Sheets option
- `backend/requirements.txt` — Remove `gspread` (keep `pandas` if used elsewhere)

### Phase 2: Backend Export Endpoints (US-1, US-2, US-3)

Build the three export endpoints with their helper modules.

**New files**:
- `backend/src/helpers/excel_generator.py` — `generate_all_meetings_excel(meetings)` and `generate_single_meeting_excel(meeting)` returning `BytesIO`
- `backend/src/helpers/pdf_generator.py` — `generate_meeting_pdf(meeting)` returning `BytesIO`
- `backend/src/routes/export.py` — FastAPI router with 3 GET endpoints using `StreamingResponse`

**Key design decisions**:
- Title fallback logic: `meeting.title or f"{meeting.platform or 'Meeting'} — {meeting.created_at.strftime('%b %d, %Y')}"`
- Participants extraction: `[s['speaker'] for s in (meeting.speaker_stats or {}).get('speakers', [])]`
- Filter: `Meeting.find(Meeting.status == MeetingStatus.COMPLETED)`
- Response: `StreamingResponse(buffer, media_type=..., headers={"Content-Disposition": ...})`

### Phase 3: Backend Tests (TDD — Constitution I)

Write tests before or alongside implementation:
- `test_excel_generator.py` — Unit tests for Excel generation (mock meeting data → validate workbook content)
- `test_pdf_generator.py` — Unit tests for PDF generation (mock meeting data → validate PDF bytes are valid)
- `test_export.py` — Integration tests for export endpoints (FastAPI TestClient → assert status codes, content types, headers)

### Phase 4: Frontend Export Buttons & API Client

Add export UI and download logic:
- `frontend/src/lib/api.ts` — Add `exportAllMeetingsExcel()`, `exportMeetingExcel(id)`, `exportMeetingPdf(id)` using fetch + blob download pattern
- `frontend/src/app/history/page.tsx` — Add "Export All Meetings as Excel" button in header area
- `frontend/src/app/history/[id]/page.tsx` — Add "Export as PDF" and "Export as Excel" buttons in header area
- Loading states and error handling via existing `useToast` pattern

## Complexity Tracking

No constitution violations. No complexity justifications needed.
