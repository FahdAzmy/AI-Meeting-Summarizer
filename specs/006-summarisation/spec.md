# Feature Specification: Summarisation & Analysis Module

**Feature Branch**: `006-summarisation`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Summarisation & Analysis Module based on SPEC-04_Summarisation.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Actionable Meeting Summaries (Priority: P1 - MVP)

Users need the lengthy literal text of a transcribed meeting converted into a concise, easily readable summary highlighting what was discussed, the key outcomes, and concrete decisions.

**Why this priority**: Reading a 60-page raw transcript defeats the purpose of an AI assistant. Producing a structured abstract is the primary value proposition of the entire product.

**Independent Test**: Can be tested independently by supplying a mock raw transcript to the module and verifying the system returns an overview, key points, and a list of decisions.

**Acceptance Scenarios**:

1. **Given** a raw meeting transcript, **When** the pipeline requests a summary, **Then** the AI assistant generates a structured report containing a 2-3 sentence overview.
2. **Given** a raw meeting transcript, **When** the pipeline requests a summary, **Then** the report includes a bulleted list of key discussion points.
3. **Given** a raw meeting transcript involving multiple choices, **When** the pipeline requests a summary, **Then** the report explicitly extracts and numbers "Decisions Made".

---

### User Story 2 - Automated Task Extraction (Priority: P1 - MVP)

Users need the AI to identify explicitly who promised to do what by when, so that action items are automatically cataloged rather than forgotten in the noise of conversation.

**Why this priority**: Accountability is the second core value proposition. Converting conversational promises into trackable data entities drives productivity.

**Independent Test**: Can be tested independently by providing a mock transcript containing explicit phrases like "Alice, please send the report by Friday" and validating the generated structured JSON maps this correctly.

**Acceptance Scenarios**:

1. **Given** a transcript containing assigned tasks, **When** the AI analyzes the text, **Then** it produces a structured list identifying the "Assignee", the "Task", and an optional "Deadline".
2. **Given** a transcript containing unresolved issues, **When** the AI analyzes the text, **Then** it produces a bulleted list of "Follow-Up Required" items demanding future attention.

---

### User Story 3 - Speaker Participation Analytics (Priority: P2)

Users scheduling team meetings need to visualize how equitable the conversation was, identifying who dominated the floor and who might need more opportunities to speak.

**Why this priority**: Provides deeper analytical value beyond text summarization, allowing managers to improve meeting culture.

**Independent Test**: Supply a transcript with pre-computed math regarding speaker lengths and assert the module correctly identifies the most active speaker and percentage shares.

**Acceptance Scenarios**:

1. **Given** a transcript with diarized speaker segments (e.g., Speaker 1, Speaker 2), **When** the analysis runs, **Then** the system calculates the total speaking time (in seconds) for each distinct speaker.
2. **Given** the calculated speaking times, **When** compiling the final report, **Then** the system accurately notes the "Most Active Speaker" and each speaker's percentage share of the total meeting duration.
3. **Given** a transcript lacking diarization data entirely, **When** the analysis runs, **Then** the system gracefully skips the speaker statistics section entirely without crashing.

---

### User Story 4 - High-Speed Delivery (Priority: P2)

Users expect summaries to be delivered significantly faster than the time it took to hold the meeting.

**Why this priority**: A 60-minute meeting should not require 60 minutes of AI processing. Fast turnaround times (e.g., getting the summary before walking back to the desk) create a "wow" factor.

**Independent Test**: Execute the full summary pipeline on a known standard length transcript and assert the execution latency.

**Acceptance Scenarios**:

1. **Given** a standard 30-minute meeting transcript, **When** the summarization logic invokes, **Then** the entire module completes the extraction and structuring within 2 minutes.
2. **Given** the broader application architecture, **When** the meeting ends, **Then** the total post-processing time (audio transcription + summarization) takes less than 10 minutes combined.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ingest a completed transcription object and utilize a Large Language Model (LLM) to perform the semantic analysis.
- **FR-002**: The LLM MUST be explicitly constrained to factual extraction (low creativity) to prevent hallucinations of meeting events that didn't occur.
- **FR-003**: The system MUST explicitly parse the AI output to reliably extract structured tasks (Assignee, Task, Deadline) separate from the general summary text.
- **FR-004**: The system MUST mathematically compute participation percentages based purely on the timestamped segments provided by the transcription layer.
- **FR-005**: The system MUST implement error handling managing LLM API timeouts or parsing failures, ensuring clear failure reasons are reported to the pipeline orchestrator.
- **FR-006**: The system MUST immediately reject summarization efforts if provided an empty transcript.

### Key Entities

- **MeetingReport**: The final aggregated data payload containing the markdown summary, structured task arrays, decisions, and speaker analytics.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system consistently generates all 5 required structural sections (Overview, Key Points, Decisions, Action Items, Follow-ups) given a healthy transcript.
- **SC-002**: The system successfully formats isolated tasks cleanly into machine-readable arrays (JSON) instead of plain paragraphs 99% of the time.
- **SC-003**: The module successfully processes 30 minutes of standard meeting dialogue into a completed payload in under 120 seconds.
- **SC-004**: The system correctly handles downstream transcription failures natively bypassing analysis on 0-byte strings.
