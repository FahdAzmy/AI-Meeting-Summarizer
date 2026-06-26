# Research: Meeting Export (Excel & PDF)

**Branch**: `010-meeting-export` | **Date**: 2026-04-26

## R1: Excel Generation Library for Python

**Decision**: Use `openpyxl` for Excel (.xlsx) file generation.

**Rationale**: `openpyxl` is the de facto standard for generating `.xlsx` files in Python. It supports styled headers, column auto-sizing, and in-memory `BytesIO` generation needed for streaming responses. It has no C-extension requirements, keeping deployment simple. The project already uses `pandas` (which itself uses openpyxl as a backend), but direct openpyxl usage gives more control over formatting.

**Alternatives considered**:
- `xlsxwriter` — Write-only, slightly faster for large files but less ecosystem integration. Lacks read support if ever needed.
- `pandas.to_excel()` — Higher-level API but less control over cell formatting, headers, and column widths. Would add unnecessary overhead for simple row generation.
- CSV export — Not an actual Excel format, loses formatting, and the spec explicitly requires `.xlsx`.

## R2: PDF Generation Library for Python

**Decision**: Use `reportlab` for structured PDF generation.

**Rationale**: `reportlab` is the most mature Python PDF library, offering full control over document layout, sections, tables, fonts, and page breaks. It supports building PDFs in-memory via `BytesIO` for streaming. It handles the structured, multi-section document layout required by the spec (title header, participants, summary, decisions, action items, follow-up, transcript).

**Alternatives considered**:
- `weasyprint` — HTML-to-PDF converter. Requires system-level dependencies (cairo, pango) which complicate deployment. Heavier than needed.
- `fpdf2` — Lighter than reportlab but less mature for complex table layouts and multi-section documents.
- `pdfkit` / `wkhtmltopdf` — Requires external binary. Not suitable for server deployment without extra system dependencies.

## R3: FastAPI Streaming File Response Pattern

**Decision**: Use `StreamingResponse` with `BytesIO` buffer for file downloads.

**Rationale**: FastAPI's `StreamingResponse` with `Content-Disposition: attachment` headers is the standard pattern for file downloads. Generating files in-memory avoids filesystem I/O and cleanup. This matches the async architecture mandated by Constitution Principle III.

**Alternatives considered**:
- `FileResponse` with temp files — Adds filesystem overhead and requires cleanup logic.
- Base64-encoded JSON response — Inefficient, increases payload size by ~33%, and requires client-side decoding.

## R4: Google Sheets Removal Scope

**Decision**: Full removal of all Google Sheets code paths, configuration, and dependencies.

**Files requiring changes** (identified via codebase grep):

| File | Change |
|------|--------|
| `backend/modules/output_storage.py` | Remove `_store_to_sheets()`, `_write_csv_fallback()`, `gspread` import, `google_sheets` from `_VALID_BACKENDS`, Sheets config fields from `__init__` |
| `backend/modules/storage_errors.py` | Remove `SheetsWriteError`, `google_sheets` from `VALID_BACKENDS` |
| `backend/config/settings.py` | Remove `GOOGLE_SHEETS_ID`, `GOOGLE_CREDENTIALS_PATH` fields |
| `backend/src/orchestrator.py` | Remove `sheets` → `google_sheets` mapping from `backend_map` |
| `backend/tests/unit/test_output_storage.py` | Remove all `google_sheets` test cases |
| `frontend/src/lib/types.ts` | Remove `'google_sheets'` from `StorageBackend` type |
| `frontend/src/components/settings/StorageToggle.tsx` | Remove `google_sheets` option from toggle |
| `backend/requirements.txt` | Remove `gspread` dependency |

**Rationale**: Clean removal ensures no dead code, no unnecessary dependencies, and no configuration confusion. The `gspread` and `pandas` (for CSV fallback) imports can be removed from `output_storage.py`. Note: `pandas` may still be needed elsewhere — verify before removing from `requirements.txt`.

## R5: Frontend Download Pattern

**Decision**: Use `window.location.href` or `fetch()` + `blob` download for triggering file downloads.

**Rationale**: For simple file downloads from authenticated endpoints, the fetch + blob pattern gives the most control: it allows showing loading states, handling errors, and triggering the browser download dialog programmatically. The pattern:
1. Frontend calls `fetch(exportUrl)` 
2. Receives blob response
3. Creates object URL and triggers download via invisible `<a>` link click
4. Revokes object URL after download

**Alternatives considered**:
- Direct `<a href>` link — Simpler but no loading state feedback and no error handling.
- `window.open()` — Opens new tab briefly, less clean UX.

## R6: Meeting Title Fallback Strategy

**Decision**: Generate fallback title server-side using `[Platform] — [Date]` format.

**Rationale**: Computing the fallback in the export endpoint keeps the logic centralized. The format `"Google Meet — Apr 26, 2026"` uses the `platform` and `created_at` fields from the Meeting model, both of which are always populated.
