# Feature Specification: Frontend Dashboard

**Feature Branch**: `002-frontend-dashboard`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Frontend Dashboard for AI Meeting Assistant based on SPEC-00_Frontend_Dashboard.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Join a Meeting via Dashboard (Priority: P1 - MVP)

Users need a central entry point where they can submit a virtual meeting link along with the participants' email addresses to initiate the AI assistant pipeline. 

**Why this priority**: Without the ability to submit a meeting and start the pipeline, none of the other features (history, details) will have data. This is the core functionality.

**Independent Test**: Can be independently tested by filling out the dashboard form, clicking "Join Meeting", and verifying the request is sent and the UI transitions to a polling state that displays real-time status updates without full page reloads.

**Acceptance Scenarios**:

1. **Given** the user is on the root Dashboard page, **When** they paste a supported meeting link (Google Meet, Zoom, Teams), **Then** the UI displays an auto-detected platform badge.
2. **Given** valid form inputs, **When** the user clicks "Join Meeting", **Then** the pipeline starts, the form is replaced/augmented by a live status panel, and polling for real-time progress begins.
3. **Given** the live status panel reaches "completed", **Then** the user is shown a success notification and a clear call-to-action to view the history.

---

### User Story 2 - Browse Meeting History (Priority: P2)

Users need to see a chronological list of their past AI-processed meetings to quickly locate a specific session.

**Why this priority**: Once meetings are processed, users need a way to find and access them. This provides the primary navigation structure to historical data.

**Independent Test**: Can be tested independently by mocking the history API endpoint to return a list of meetings. The table should correctly render, and client-side sorting should function on columns like Date, Platform, Duration, and Status.

**Acceptance Scenarios**:

1. **Given** the user navigates to the History page, **When** the list of meetings is retrieved, **Then** an organized table displays Date, Platform, Duration, a short Summary preview, and Status.
2. **Given** a populated meeting table, **When** the user clicks column headers (e.g., Date or Status), **Then** the table sorts its contents immediately without refreshing the page.
3. **Given** a meeting row, **When** the user clicks "View Details", **Then** they are navigated to the explicit detail view for that meeting.

---

### User Story 3 - View Detailed Meeting Analysis (Priority: P3)

Users need to deeply explore the outputs of a completed meeting, including the full text summary, decisions, task assignments, and verbatim transcript.

**Why this priority**: The primary value of the entire application is consuming the final generated artifacts. This view presents the core output to the end-user.

**Independent Test**: Can be fully tested by navigating to the detail route with a mocked meeting ID that returns complete summary, action items, and diarization payload. The UI should successfully parse and render all sections dynamically.

**Acceptance Scenarios**:

1. **Given** an existing meeting record, **When** the user views its detail page, **Then** all segments (Overview, Summary, Action Items, Decisions, Speaker Stats) are rendered.
2. **Given** the transcript section is loaded, **When** the user clicks a toggle control, **Then** the verbatim transcript can be expanded or collapsed.
3. **Given** a meeting ID that does not exist, **When** the user navigates to its detail page, **Then** the system presents a clear, user-friendly "Meeting not found" error.

---

### User Story 4 - System Settings Configuration (Priority: P4)

Users need to configure global preferences that govern how the backend pipeline behaves (e.g., overriding the STT provider or storage location).

**Why this priority**: While necessary for customization, the system can function using out-of-the-box defaults while the core workflows (P1-P3) are being proven out.

**Independent Test**: Can be tested independently by changing a toggle on the settings screen, saving the changes, and refreshing the page to verify the system persisted the options correctly.

**Acceptance Scenarios**:

1. **Given** the settings page is accessed, **When** it loads, **Then** it reflects the currently active configuration from the system.
2. **Given** the user modifies the storage provider or email credentials, **When** they submit the form, **Then** the system displays a confirmation message indicating changes are saved.
3. **Given** saved settings, **When** the next meeting pipeline is initiated, **Then** those new configurations (like the newly chosen STT provider) are respected.

### Edge Cases

- What happens when a user submits an invalid or unsupported meeting URL? (Should fail client-side validation immediately).
- How does the system handle a network disconnect while polling for real-time meeting status? (Should show a connection error and gracefully attempt to reconnect).
- What happens when the backend API is entirely unreachable? (Should display clear error boundaries and friendly failure states instead of a blank UI).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a dashboard view accepting a meeting URL and a comma-separated list of participant emails.
- **FR-002**: System MUST validate the format of the meeting link and the comma-separated emails client-side before sending requests.
- **FR-003**: System MUST auto-detect the platform (Google Meet, Zoom, Teams) based on the provided URL structure.
- **FR-004**: System MUST display real-time pipeline status updates while processing an active meeting by periodically checking the status endpoint.
- **FR-005**: System MUST display a sortable overview table of historical meetings containing Date, Platform, Duration, Summary snippet, and Status.
- **FR-006**: System MUST provide a dedicated meeting view that clearly separates and structures the generated Summary, Action Items table, Decisions list, and scrollable verbatim Transcript.
- **FR-007**: System MUST provide an interface to configure systemic settings, limited to storage backend (Database vs. Google Sheets), STT provider, and email sender credentials.
- **FR-008**: System MUST utilize asynchronous communication patterns against a distinct API layer (no tight coupling to backend implementation).

### Key Entities

- **Meeting**: Represents a single recorded session. Contains identifiers, original join link, detected platform, duration, participant list, transcript payload, structured summary payload, execution status, and storage destination.
- **Settings**: Represents a global singleton configuration governing the system. Contains storage preference, STT provider preference, and email credentials.
- **ActionItem**: Extracted micro-entity belonging to a Meeting containing an assignee, task description, and deadline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can successfully initiate a meeting pipeline flow in under 3 clicks starting from the Dashboard.
- **SC-002**: Client-side validation prevents 100% of malformed meeting links or invalid email string formats from reaching the backend API.
- **SC-003**: The historical meeting table renders datasets of up to 100 records in under 2 seconds.
- **SC-004**: System status polling reflects backend progress with a maximum visual latency of 3 seconds.
- **SC-005**: The entire interface is responsive and fully functional down to a minimum device width of 375px without horizontal scrolling issues.
- **SC-006**: 100% of API communication failures surface an explicit, non-technical error notification to the user rather than failing silently.
