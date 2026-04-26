# Quickstart: Meeting Export (Excel & PDF)

**Branch**: `010-meeting-export` | **Date**: 2026-04-26

## Prerequisites

- Python 3.11+ with the backend virtual environment active
- Node.js 18+ with frontend dependencies installed
- MongoDB running locally or accessible via `MONGO_URI`
- At least one meeting with `status: completed` in the database

## Setup

### 1. Install new backend dependencies

```bash
cd backend
pip install openpyxl reportlab
```

### 2. Start the backend

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

### 3. Start the frontend

```bash
cd frontend
npm run dev
```

## Testing the Feature

### Export All Meetings (Excel)

1. Navigate to `http://localhost:3000/history`
2. Click the **"Export All Meetings as Excel"** button in the header area
3. A `.xlsx` file should download containing all completed meetings

**Or via API directly:**
```bash
curl -o meetings.xlsx http://localhost:8000/api/export/meetings/excel
```

### Export Single Meeting (PDF)

1. Navigate to `http://localhost:3000/history/{meeting-id}`
2. Click the **"Export as PDF"** button
3. A structured PDF should download with all meeting sections

**Or via API directly:**
```bash
curl -o meeting.pdf http://localhost:8000/api/export/meetings/{id}/pdf
```

### Export Single Meeting (Excel)

1. Navigate to `http://localhost:3000/history/{meeting-id}`
2. Click the **"Export as Excel"** button
3. A `.xlsx` file should download with that meeting's data

**Or via API directly:**
```bash
curl -o meeting.xlsx http://localhost:8000/api/export/meetings/{id}/excel
```

### Verify Google Sheets Removal

1. Check that the Settings page no longer shows a "Google Sheets" storage option
2. Confirm the pipeline runs without any Google API credentials configured
3. Run: `grep -r "google_sheets" backend/` — should return zero results

## Running Tests

```bash
cd backend
pytest tests/unit/test_export.py -v
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/routes/export.py` | New export API endpoints |
| `backend/src/helpers/excel_generator.py` | Excel file generation logic |
| `backend/src/helpers/pdf_generator.py` | PDF file generation logic |
| `frontend/src/app/history/page.tsx` | History page (+ export button) |
| `frontend/src/app/history/[id]/page.tsx` | Meeting detail page (+ export buttons) |
| `frontend/src/lib/api.ts` | API client (+ export methods) |
