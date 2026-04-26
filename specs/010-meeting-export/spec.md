# Feature Specification: Meeting Export (Excel & PDF)

**Feature Branch**: `010-meeting-export`  
**Created**: 2026-04-26  
**Status**: Draft  
**Input**: User description: "Delete Google Sheets save, build export endpoints that export meetings from database as Excel. History page has an 'Export All Meetings as Excel' button. Specific meeting page (history/id) has two buttons: Export as PDF (structured PDF with all meeting data) and Export as Excel. PDF is for one meeting only; Excel works for both all meetings and a single meeting."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export All Meetings as Excel (Priority: P1)

A user navigates to the Meeting History page, where they see a list of all past meetings. They want to download a comprehensive Excel spreadsheet containing every meeting record in the system. The user clicks the **"Export All Meetings as Excel"** button. The system fetches all meeting data from the database, generates an Excel file with well-structured columns (meeting title, date, duration, participants, summary, decisions, action items), and triggers a browser download of the file.

**Why this priority**: Bulk data export is essential for reporting, compliance, and offline analysis. It enables stakeholders to review all meeting intelligence in one document without manually visiting each meeting.

**Independent Test**: Can be tested by creating multiple mock meeting records in the database, clicking the export button on the history page, and verifying the downloaded Excel file contains all meetings with correctly populated columns.

**Acceptance Scenarios**:

1. **Given** the user is on the Meeting History page with 5 or more meetings stored, **When** they click "Export All Meetings as Excel", **Then** the browser downloads an Excel file containing one row per meeting with columns for: meeting title, date, duration, participants, summary, decisions, and action items.
2. **Given** the user is on the Meeting History page with zero meetings stored, **When** they click "Export All Meetings as Excel", **Then** the system displays a user-friendly message indicating there are no meetings to export, and no file is downloaded.
3. **Given** the user is on the Meeting History page with 100+ meetings, **When** they click "Export All Meetings as Excel", **Then** the system shows a loading indicator while generating the file, and the download completes within a reasonable time.

---

### User Story 2 - Export Single Meeting as PDF (Priority: P1)

A user navigates to a specific meeting's detail page (`history/{id}`). They want a professional, print-ready document capturing the complete meeting record. The user clicks the **"Export as PDF"** button. The system generates a structured PDF document containing all meeting details — title, date, time, duration, participants, full transcript, AI-generated summary, key decisions, and action items — formatted in a clear, readable layout with proper headings and sections.

**Why this priority**: A structured PDF is the standard format for sharing meeting minutes with stakeholders, archiving for compliance, and distributing to people who may not have access to the application.

**Independent Test**: Can be tested by navigating to a specific meeting page that has complete data (transcript, summary, action items), clicking "Export as PDF", and verifying the downloaded PDF contains all meeting sections with proper formatting.

**Acceptance Scenarios**:

1. **Given** the user is viewing a completed meeting's detail page, **When** they click "Export as PDF", **Then** the browser downloads a PDF file that includes: a title/header section with meeting name and date, a participants section listing all attendees, a summary section, a decisions section, an action items section with assignees and deadlines (if available), a follow-up items section, and the full transcript.
2. **Given** the user is viewing a meeting that has a summary but no transcript (e.g., transcript was not generated), **When** they click "Export as PDF", **Then** the PDF is generated with all available sections and gracefully omits the missing transcript section rather than showing blank or error content.
3. **Given** the user exports a meeting as PDF, **When** the PDF is opened in any standard PDF reader, **Then** the document is well-formatted with clear section headings, readable fonts, and proper page breaks.

---

### User Story 3 - Export Single Meeting as Excel (Priority: P2)

A user navigates to a specific meeting's detail page (`history/{id}`). They want to export this particular meeting's data in a spreadsheet format for further analysis, editing, or integration with other tools. The user clicks the **"Export as Excel"** button. The system generates an Excel file containing the meeting data in structured sheets or columns.

**Why this priority**: While PDF serves the archival/sharing use case, Excel export for a single meeting allows users to manipulate, annotate, or integrate individual meeting data into their own workflows and spreadsheets.

**Independent Test**: Can be tested by navigating to a specific completed meeting, clicking "Export as Excel", and verifying the downloaded file contains that meeting's data with properly labeled columns.

**Acceptance Scenarios**:

1. **Given** the user is viewing a completed meeting's detail page, **When** they click "Export as Excel", **Then** the browser downloads an Excel file containing that single meeting's data (title, date, duration, participants, summary, decisions, action items) in a well-structured spreadsheet format.
2. **Given** the user is viewing a meeting with partial data (e.g., no action items), **When** they click "Export as Excel", **Then** the Excel file is generated with all available data and empty cells for missing fields.

---

### User Story 4 - Remove Google Sheets Export (Priority: P1)

The existing Google Sheets integration for saving meeting data is removed from the system. All references to Google Sheets export, including configuration options, code paths, and fallback CSV mechanisms tied to Sheets failures, are cleaned up.

**Why this priority**: Replacing the Google Sheets dependency simplifies the architecture, removes the need for Google API credentials, and consolidates export functionality into the new Excel/PDF endpoints which are entirely self-contained.

**Independent Test**: Can be verified by confirming that no Google Sheets configuration is required, no Google API calls are made during the meeting pipeline, and the system functions fully without any Google Sheets credentials.

**Acceptance Scenarios**:

1. **Given** the system previously had Google Sheets export configured, **When** the feature is deployed, **Then** the system no longer attempts to push data to Google Sheets and no Google Sheets related errors occur.
2. **Given** a meeting pipeline completes, **When** the storage module processes the output, **Then** data is persisted only to the application database (no external spreadsheet writes).

---

### Edge Cases

- What happens when the user exports meetings while a new meeting is actively being processed by the pipeline? → The export includes only meetings with `COMPLETED` status.
- What happens if the meeting data contains special characters or very long text (e.g., a 2-hour transcript)? → The export handles large content gracefully without truncation or corruption.
- What happens if the user's browser blocks the download? → The system provides clear feedback and does not silently fail.
- What happens if the database is temporarily unavailable during an export request? → The system returns a user-friendly error message indicating the export could not be completed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an endpoint that accepts a request and returns all meetings from the database as a downloadable Excel file.
- **FR-002**: The system MUST provide an endpoint that accepts a meeting identifier and returns that specific meeting's data as a downloadable Excel file.
- **FR-003**: The system MUST provide an endpoint that accepts a meeting identifier and returns that specific meeting's data as a downloadable PDF file.
- **FR-004**: The PDF document MUST include structured sections for: meeting title, date/time, duration, participants, AI-generated summary, key decisions, action items, follow-up items, and full transcript (when available).
- **FR-005**: The Excel file for all meetings MUST contain one row per meeting with clearly labeled columns: meeting title, date, duration, participants, summary, decisions, action items, and follow-up items.
- **FR-013**: When a meeting has no explicit title, the system MUST auto-generate a display title using the format "[Platform] — [Date]" (e.g., "Google Meet — Apr 26, 2026") for use in exports and display contexts.
- **FR-006**: The Excel file for a single meeting MUST contain that meeting's complete data in a well-structured spreadsheet format.
- **FR-007**: The Meeting History page MUST display an "Export All Meetings as Excel" button that triggers a download of the all-meetings Excel file.
- **FR-008**: The specific meeting detail page (`history/{id}`) MUST display two export buttons: "Export as PDF" and "Export as Excel".
- **FR-009**: The system MUST remove all Google Sheets export functionality, including configuration, code paths, and related fallback mechanisms (CSV fallback for Sheets failures).
- **FR-010**: Export operations MUST only include meetings with a completed status.
- **FR-011**: The system MUST show a loading indicator during export generation to inform the user that the file is being prepared.
- **FR-012**: The system MUST handle missing or partial meeting data gracefully during export, omitting unavailable sections rather than showing errors or blank placeholders.

### Key Entities

- **Meeting Record**: The core data entity containing title, date, duration, participants, transcript, summary, decisions, and action items — sourced from the application database.
- **Export File**: A generated document (Excel or PDF) created on-demand from meeting records, delivered as a browser download.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can export all meetings as an Excel file within 10 seconds for datasets of up to 200 meetings.
- **SC-002**: Users can export a single meeting as a PDF in under 5 seconds.
- **SC-003**: Users can export a single meeting as an Excel file in under 3 seconds.
- **SC-004**: 100% of completed meetings are accurately represented in the exported Excel file with no data loss or corruption.
- **SC-005**: The exported PDF is readable and properly formatted when opened in any standard PDF viewer.
- **SC-006**: All Google Sheets export code is fully removed with zero references remaining in the codebase.
- **SC-007**: 95% of users successfully complete an export operation on their first attempt without needing assistance.

## Assumptions

- The application database already contains meeting records with the required fields (title, date, duration, participants, transcript, summary, decisions, action items).
- The frontend uses the existing Next.js framework and communicates with the backend via the established REST API pattern.
- The backend uses the existing FastAPI/Python stack with access to the MongoDB database.
- Export files are generated server-side and streamed to the client as file downloads.
- No authentication changes are required — the export endpoints follow the existing authentication pattern of the application.
- The existing database save (FR-002 in the output-storage spec) remains fully intact; only the Google Sheets portion is removed.
- Email distribution functionality (User Story 2 in output-storage spec) remains unchanged.

## Clarifications

### Session 2026-04-26

- Q: What should be used as the meeting identifier in exports when the title field is null? → A: Auto-generate a fallback title from date + platform (e.g., "Google Meet — Apr 26, 2026") when title is missing.
- Q: Should the `follow_up` field from the data model be included in exports? → A: Yes — include follow-up items as a dedicated section in PDF and a dedicated column in Excel exports.
- Q: Should the PDF support right-to-left (RTL) text for Arabic content? → A: No — LTR only, English content assumed.
