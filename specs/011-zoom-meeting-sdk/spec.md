# Feature Specification: Zoom Meeting SDK Integration

**Feature Branch**: `011-zoom-meeting-sdk`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "Zoom Meeting SDK integration for reliable Zoom meeting join — replace the current fragile browser-automation approach with Zoom's official Meeting SDK to join meetings programmatically, detect meeting end natively, and maintain multi-platform support."

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Reliable Zoom Meeting Join (Priority: P1 - MVP)

Users need the AI Meeting Assistant to join Zoom meetings reliably every time. The current approach has a ~60-70% success rate because it relies on scraping the Zoom web interface — selectors break when Zoom updates their UI, automated browsers are actively blocked, and the "Open Zoom App" redirect prompt must be intercepted. Users lose trust when meetings fail to be captured.

The new approach uses Zoom's official programmatic meeting join method, which authenticates the bot as a registered application rather than a guest browser. This eliminates all UI-scraping fragility and brings the join success rate to >95%.

**Why this priority**: Without reliably entering the meeting room, no downstream pipeline stage (recording, transcription, summarisation, delivery) can execute. This is the single most impactful improvement to the system's overall reliability for Zoom meetings.

**Independent Test**: Can be tested independently by providing a valid Zoom meeting link and verifying the AI assistant joins the meeting room successfully, with its display name visible in the participant list, without any manual intervention.

**Acceptance Scenarios**:

1. **Given** a valid Zoom meeting link, **When** the user submits it through the dashboard, **Then** the system automatically extracts the meeting identifier, authenticates itself as a registered Zoom application, and joins the meeting as "AI Summarizer" within 15 seconds.
2. **Given** a Zoom meeting with a waiting room enabled, **When** the assistant enters the waiting room, **Then** the system waits up to 5 minutes for host admission. If admitted, it joins and signals success. If the 5-minute timeout expires, the system raises a clear "Waiting Room Timeout" error and notifies the user.
3. **Given** valid application credentials are configured, **When** the system requests a meeting-join authorisation token, **Then** the token is generated and returned in under 100 milliseconds.
4. **Given** the user submits a Zoom meeting link from the dashboard, **When** the system opens the SDK meeting page, **Then** the meeting page runs in the background and the user remains on the dashboard, monitoring progress via the existing status indicators.

---

### User Story 2 – Native Meeting End Detection (Priority: P1 - MVP)

Users rely on prompt post-meeting processing (transcription, summary, delivery). The current approach polls the meeting UI every 5 seconds to check for "meeting ended" text — this is slow (30+ seconds of lag), brittle (text patterns change across Zoom versions), and wasteful.

The new approach uses the SDK's native event-driven callbacks, which fire instantly when the meeting ends — eliminating polling entirely and reducing detection lag from 30+ seconds to under 5 seconds.

**Why this priority**: Delayed or missed end-detection is the second-largest source of pipeline failures. Event-driven detection is fundamentally more reliable and eliminates an entire class of bugs.

**Independent Test**: Can be tested independently by joining a test meeting, then ending it from the host side, and verifying the system detects the end event within 5 seconds and triggers post-meeting processing.

**Acceptance Scenarios**:

1. **Given** the AI Summarizer is in an active Zoom meeting, **When** the meeting host ends the call for all participants, **Then** the system detects the meeting-end event and begins post-meeting processing (recording stop, transcription, summarisation) within 5 seconds.
2. **Given** the AI Summarizer is the only participant remaining in the meeting, **When** a 30-second grace period elapses (to handle brief disconnections), **Then** the system concludes the meeting has ended and begins post-meeting processing.
3. **Given** the SDK fires a meeting-end event, **When** the system processes it, **Then** the pipeline status in the database transitions from "recording" to "transcribing" within 10 seconds.

---

### User Story 3 – Zoom Meeting Link Parsing (Priority: P1 - MVP)

Users paste Zoom links in various formats. The system must reliably extract the meeting identifier and optional passcode from any valid Zoom URL to feed into the programmatic join flow.

**Why this priority**: Without correct URL parsing, the system cannot extract the meeting identifier needed to join. This is a prerequisite for User Story 1.

**Independent Test**: Can be tested independently with a suite of different Zoom URL formats, verifying correct extraction of meeting identifiers and passcodes for each.

**Acceptance Scenarios**:

1. **Given** a standard Zoom URL (e.g., `https://zoom.us/j/1234567890?pwd=abc123`), **When** the system parses it, **Then** it correctly extracts the meeting identifier `1234567890` and passcode `abc123`.
2. **Given** a Zoom URL with a company subdomain (e.g., `https://company.zoom.us/j/9876543210`), **When** the system parses it, **Then** it correctly extracts the meeting identifier `9876543210` with an empty passcode.
3. **Given** an unsupported or malformed Zoom URL (e.g., a vanity URL like `https://zoom.us/my/username`), **When** the system attempts to parse it, **Then** it raises a clear, descriptive error before attempting to join.

---

### User Story 4 – Multi-Platform Coexistence (Priority: P2)

The system currently supports Google Meet, Zoom, and Microsoft Teams. The new Zoom SDK integration must coexist with the existing browser-automation flows for Google Meet and Teams, which do not have equivalent SDKs.

**Why this priority**: Users expect all three platforms to keep working. The Zoom SDK upgrade must be an enhancement, not a regression for other platforms.

**Independent Test**: Can be tested by submitting links for all three platforms and verifying each joins through its expected flow — the new approach for Zoom and the existing approach for Google Meet and Teams.

**Acceptance Scenarios**:

1. **Given** a Google Meet URL, **When** submitted to the pipeline, **Then** the system uses the existing browser-automation join flow (no change in behaviour).
2. **Given** a Zoom URL and valid Zoom application credentials, **When** submitted to the pipeline, **Then** the system routes to the new SDK-based join flow.
3. **Given** a Microsoft Teams URL, **When** submitted to the pipeline, **Then** the system uses the existing browser-automation join flow (no change in behaviour).
4. **Given** a Zoom URL but **without** valid application credentials configured, **When** submitted to the pipeline, **Then** the system gracefully falls back to the existing browser-automation Zoom join with a warning log.

---

### User Story 5 – Secure Credential Management (Priority: P2)

Application credentials (Client ID and Client Secret) must be managed securely. The secret must never be exposed in the user-facing interface, network traffic, or browser code.

**Why this priority**: Credential leakage would allow unauthorized parties to impersonate the application and join meetings on its behalf, posing a significant security and privacy risk.

**Independent Test**: Can be tested by inspecting the frontend bundle, API responses, and browser network traffic to verify the secret is never transmitted or included.

**Acceptance Scenarios**:

1. **Given** the system is configured with Zoom application credentials, **When** the frontend requests a meeting-join authorisation token, **Then** only the token and the public Client ID are returned — the Client Secret is never included in any response.
2. **Given** a developer inspects the frontend source code (built bundle), **When** they search for the Client Secret value, **Then** it is not present anywhere in the frontend code or assets.

### Edge Cases

- What happens if the Zoom application credentials are not configured in the environment? → The system falls back to the existing browser-automation Zoom join and logs a warning.
- What happens if the SDK fails to initialise (e.g., network error loading assets)? → The system retries once, then falls back to browser-automation with error logging.
- What happens if the meeting requires authenticated Zoom users only (no guest access)? → The system logs a clear error message explaining the limitation and marks the meeting as "failed" with a descriptive reason.
- What happens if the meeting link is a Zoom vanity URL without a numeric identifier? → The system raises a descriptive error before attempting to join and notifies the user.
- What happens if multiple Zoom meetings run concurrently? → Each meeting operates in its own isolated session; the system supports at least 3 concurrent Zoom meetings.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST authenticate itself as a registered Zoom application using a secure, short-lived token (expiry ≤ 2 hours) generated on the server side, so that it can join Zoom meetings programmatically without browser-automation fragility.
- **FR-002**: The system MUST expose a public endpoint (no authentication required) that accepts a meeting identifier and returns a time-limited authorisation token for the Zoom SDK, responding in under 100 milliseconds.
- **FR-003**: The system MUST parse Zoom meeting URLs in all standard formats (with/without subdomains, with/without passcodes) and extract the numeric meeting identifier and optional passcode.
- **FR-004**: The system MUST embed the Zoom meeting experience in a dedicated background page (opened automatically by the system, not visible to the user) that programmatically initialises the SDK, joins the meeting, and captures meeting lifecycle events (join, end, participant changes). The user remains on the dashboard and monitors progress via existing status indicators.
- **FR-005**: The system MUST detect when a Zoom meeting ends — either by host action or by the assistant being alone for 30 seconds — and immediately notify the backend to trigger post-meeting processing.
- **FR-006**: The system MUST store Zoom application credentials (Client ID and Client Secret) as environment variables, consistent with the existing configuration management pattern.
- **FR-007**: The system MUST detect Zoom URLs and route them through the SDK-based join path, while preserving the existing browser-automation paths for Google Meet and Microsoft Teams.
- **FR-008**: The system MUST implement a graceful fallback to the existing browser-automation Zoom join if SDK credentials are not configured or SDK initialisation fails.
- **FR-009**: The system MUST continue using the existing external audio capture mechanism for recording Zoom meetings, as the SDK does not provide raw audio access.
- **FR-010**: The system MUST surface clear, actionable error messages to the user when a Zoom meeting fails to join (e.g., "Waiting Room Timeout", "Invalid Meeting Link", "Authentication Required").

### Key Entities

- **Zoom Application Credentials**: A pair of secrets (Client ID + Client Secret) obtained by registering a "General App" with Meeting SDK enabled on the Zoom Marketplace. The Client ID identifies the application publicly; the Client Secret is used exclusively on the backend to sign authorisation tokens.
- **Authorisation Token**: A short-lived, meeting-specific token generated on the server, sent to the frontend SDK to authenticate the meeting join. Cannot be reused for different meetings.
- **Meeting Identifier**: A numeric ID (e.g., `1234567890`) extracted from Zoom URLs, required by the SDK to join a specific meeting.
- **Passcode**: An optional alphanumeric string extracted from Zoom URLs (`?pwd=...`), required by some meetings for entry.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zoom meetings join successfully at a >95% rate (up from the current ~60-70% with browser automation), measured across 20 consecutive test meetings.
- **SC-002**: Meeting-end detection triggers post-meeting processing within 5 seconds of the meeting ending (down from 30+ seconds with the current polling approach).
- **SC-003**: All existing Google Meet and Microsoft Teams meeting flows continue working with zero regressions — no change in behaviour or success rate.
- **SC-004**: The authorisation token is generated and returned to the frontend in under 100 milliseconds.
- **SC-005**: The Zoom application Client Secret never appears in the frontend bundle, browser network requests, or any user-facing output.
- **SC-006**: Users receive a clear, actionable error message within 10 seconds when a Zoom meeting join fails, including the specific failure reason (e.g., "Waiting Room Timeout after 5 minutes", "Invalid meeting link format").

## Assumptions

- The team has access to a Zoom Developer account with Owner or Admin permissions to create a Meeting SDK App on the Zoom App Marketplace.
- The frontend application runs in a visible browser window (not headless) since the Zoom Meeting SDK requires DOM rendering.
- OBS-based audio capture continues to be the recording mechanism for all platforms, including Zoom.
- The system will join meetings as an attendee (role 0), not as a host. Hosting meetings is out of scope.
- Zoom Meeting SDK App approval for production use is handled separately as an administrative task, not a development task.

## Clarifications

### Session 2026-05-03

- Q: Should the token-generation endpoint require authentication (user session, API key) or be publicly accessible? → A: Public — no authentication required.
- Q: Should the SDK meeting page be visible to the user or run in the background? → A: Background — system opens the meeting page automatically; user stays on the dashboard monitoring status.
- Q: Should the bot's display name ("AI Summarizer") be fixed or configurable? → A: Fixed — always joins as "AI Summarizer".
