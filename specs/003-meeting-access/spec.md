# Feature Specification: Meeting Access Module

**Feature Branch**: `003-meeting-access`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Meeting Access Module based on SPEC-01_Meeting_Access.md (Selenium bot platform navigation and failure notifications)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Join Supported Meetings Automatically (Priority: P1 - MVP)

Users need the AI Meeting Assistant to automatically navigate to and successfully join Google Meet, Zoom, or Microsoft Teams sessions without requiring human intervention (such as manually accepting camera/mic prompts or clicking "Join").

**Why this priority**: Without the ability to enter the virtual meeting room, the system cannot capture audio or perform any downstream transcriptions or summaries. This forms the foundational step of the AI pipeline.

**Independent Test**: Can be tested independently by supplying valid meeting URLs for each supported platform to the module and verifying that the simulated user appears in the meeting participant list.

**Acceptance Scenarios**:

1. **Given** a valid Google Meet URL, **When** the pipeline initiates join protocols, **Then** the bot dismisses pre-join dialogs, mutes its own mic/cam, and successfully clicks "Join now".
2. **Given** a valid Zoom web client URL, **When** the pipeline initiates join protocols, **Then** the bot enters a display name, clicks "Join", and accurately waits in the waiting room until admitted by the host.
3. **Given** a valid Microsoft Teams URL, **When** the pipeline initiates join protocols, **Then** the bot selects the browser-only experience, mutes devices, and joins the session.

---

### User Story 2 - Autonomous Meeting End Detection (Priority: P2)

Users rely on the assistant to run indefinitely during a meeting but immediately begin processing results the moment the meeting concludes.

**Why this priority**: Processing requires the full session to be complete. Recognizing the end of a meeting frees up system resources and allows the final report generation to be fast and proactive.

**Independent Test**: Can be tested independently by creating a test meeting room, admitting the bot, and then intentionally ending the meeting for all participants to verify the bot triggers the completion signals.

**Acceptance Scenarios**:

1. **Given** an active Google Meet session with the AI Assistant present, **When** the meeting host ends the call for everyone, **Then** the system detects the "Meeting ended" UI signal and returns control logic to the pipeline gracefully.
2. **Given** an active Zoom session with the AI Assistant present, **When** the host ends the call or the bot is removed, **Then** the system detects the disconnection dialog or URL change and returns control logic gracefully.
3. **Given** an active Teams session with the AI Assistant present, **When** the meeting ends, **Then** the system detects the "call-ended" data attribute banner and returns control logic gracefully.

---

### User Story 3 - Comprehensive Failure Notifications (Priority: P3)

If the AI Assistant cannot join a meeting (due to invalid links, unexpected UI changes, or waiting room timeouts), users must be immediately notified of the failure rather than leaving the system hanging in an infinite "processing" loop.

**Why this priority**: Silent failures erode user trust. Proactively emailing participants and updating the external dashboard prevents users from waiting for summaries that will never arrive.

**Independent Test**: Can be tested independently by providing an expired meeting link or purposely blocking the bot in a waiting room to trigger the failure threshold, then verifying the email payload and status update correctly fire.

**Acceptance Scenarios**:

1. **Given** the bot encounters a blocking issue preventing it from joining, **When** it exhausts its maximum retry policy, **Then** the meeting status is formally marked as "failed" alongside a human-readable failure reason.
2. **Given** a final failure state, **When** the system resolves the failure, **Then** an automated email is sent to all participants detailing the meeting link, platform, timestamp, and specific failure reason.
3. **Given** a final failure state, **When** the system resolves the failure, **Then** the real-time status API broadcasts a failure message that will render a red alert banner and a "Retry" prompt on the user-facing dashboard.

### Edge Cases

- What happens when a user submits an unsupported platform link (e.g., WebEx)? (The system must fail early with an "Unsupported Platform" notification before attempting to open the link).
- What happens if the meeting continues longer than expected? (System must adhere to infrastructure timeout limits or keep running based on constraints).
- What happens if the host keeps the bot in the waiting room indefinitely? (The system must have a hard timeout boundary, e.g. 5 minutes, after which it throws a `WaitingRoomTimeout` failure).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST detect the intended video platform exclusively based on the URL structure.
- **FR-002**: The system MUST reliably click the appropriate sequences of UI elements for Google Meet, Zoom, and Teams to achieve a "joined" state.
- **FR-003**: The system MUST implement an automated retry policy (up to 3 attempts with delays) for encountering transient join errors before declaring a hard failure.
- **FR-004**: The system MUST maintain a periodic polling structure (e.g., every 30 seconds) to detect when a meeting has concluded based on distinct platform UI changes.
- **FR-005**: The system MUST send an HTML-formatted failure email to all identified participants if the maximum join retries are exhausted.
- **FR-006**: The system MUST update the tracking platform/dashboard with explicit error payloads specifying the exact nature of the failure context (e.g., "Waiting room timeout", "Join button not found").

### Key Entities

- **Platform Detection**: Identifies between Meet, Zoom, and Teams contexts.
- **Failure Notification**: Metadata block including the failure context, timestamp, requested link, and array of recipients.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system exhibits an automated join success rate of >95% for standard Google Meet, Zoom, and Microsoft Teams links.
- **SC-002**: The system correctly terminates and begins processing results via end detection within 60 seconds of a meeting being closed by the host.
- **SC-003**: 100% of final join failure scenarios result in both an email notification and a dashboard status error update.
- **SC-004**: A user waiting for a bot blocked in a waiting room receives the failure notification email in precisely 5 minutes (plus retry buffer latency).
