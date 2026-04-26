# API Contracts: Meeting Export

**Branch**: `010-meeting-export` | **Date**: 2026-04-26

## New Endpoints

### GET `/api/export/meetings/excel`

Export all completed meetings as an Excel (.xlsx) file.

**Request**: No body. No query parameters.

**Response**:
- **200 OK** — Binary `.xlsx` file download
  ```
  Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  Content-Disposition: attachment; filename="all_meetings_2026-04-26.xlsx"
  ```
- **404 Not Found** — No completed meetings exist
  ```json
  { "detail": "No completed meetings available for export." }
  ```
- **500 Internal Server Error** — Database or generation failure
  ```json
  { "detail": "Failed to generate export. Please try again." }
  ```

---

### GET `/api/export/meetings/{id}/excel`

Export a single meeting as an Excel (.xlsx) file.

**Path Parameters**:
- `id` (string, required) — MongoDB ObjectId of the meeting

**Response**:
- **200 OK** — Binary `.xlsx` file download
  ```
  Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  Content-Disposition: attachment; filename="meeting_Google_Meet_2026-04-26.xlsx"
  ```
- **404 Not Found** — Meeting not found or not completed
  ```json
  { "detail": "Meeting not found or not yet completed." }
  ```
- **500 Internal Server Error** — Generation failure
  ```json
  { "detail": "Failed to generate export. Please try again." }
  ```

---

### GET `/api/export/meetings/{id}/pdf`

Export a single meeting as a structured PDF file.

**Path Parameters**:
- `id` (string, required) — MongoDB ObjectId of the meeting

**Response**:
- **200 OK** — Binary PDF file download
  ```
  Content-Type: application/pdf
  Content-Disposition: attachment; filename="meeting_Google_Meet_2026-04-26.pdf"
  ```
- **404 Not Found** — Meeting not found or not completed
  ```json
  { "detail": "Meeting not found or not yet completed." }
  ```
- **500 Internal Server Error** — Generation failure
  ```json
  { "detail": "Failed to generate export. Please try again." }
  ```

## Modified Endpoints

### GET `/api/settings` (existing)

**Change**: Remove `google_sheets` from the `storage_backend` response. Default is now always `"database"`.

### POST `/api/settings` (existing)

**Change**: Reject `google_sheets` as a valid `storage_backend` value.

## Removed Functionality

The following are **removed** as part of Google Sheets cleanup:
- `storage: "sheets"` option in `POST /api/trigger` request body (mapped to `google_sheets` internally)
- Google Sheets configuration fields from settings endpoints

## Frontend API Client Additions

New methods to add to `frontend/src/lib/api.ts`:

```typescript
// Export all meetings as Excel
async exportAllMeetingsExcel(): Promise<void>

// Export single meeting as Excel  
async exportMeetingExcel(id: string): Promise<void>

// Export single meeting as PDF
async exportMeetingPdf(id: string): Promise<void>
```

Each method fetches the blob, creates an object URL, and triggers a browser download.
