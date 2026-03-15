# Feature Specification: Pipeline Orchestrator

**Feature Branch**: `008-pipeline-orchestrator`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Pipeline Orchestrator based on SPEC-06_Pipeline_Orchestrator.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Frictionless End-to-End Automation (Priority: P1 - MVP)

Users expect that submitting a single meeting link triggers an entirely hands-off process. They should not have to manually tell the system to start recording, then tell it to stop, then tell it to transcribe. The orchestrator must link all autonomous modules into a single, seamless flow.

**Why this priority**: Without a central manager, the individual modules (Selenium joining, OBS recording, STT transcription, LLM summary, SMTP dispatch) cannot communicate. This is the brain of the AI assistant.

**Independent Test**: Can be tested independently by providing a mock link to a dummy meeting and asserting the pipeline successfully calls the sequence of mocks for join, record, transcribe, summarize, and store.

**Acceptance Scenarios**:

1. **Given** a valid meeting URL and participant list, **When** the user submits the request, **Then** the orchestrator systematically triggers the Meeting Access, Audio Capture, Transcription, Summarisation, and Storage modules sequentially without further user input.
2. **Given** a standard 60-minute meeting concludes, **When** the bot leaves the room, **Then** all post-processing analytics (Transcription, Summarisation, Storage) perfectly conclude within 10 minutes.

---

### User Story 2 - Real-Time Dashboard Visibility (Priority: P1 - MVP)

Users managing multiple bots across different meetings need to know exactly what the bot is doing at any given second. If the bot is stuck connecting, or actively transcribing, the web dashboard must reflect this state immediately.

**Why this priority**: Users lose trust in automation if it appears to be a "black box". Transparent progression statuses reduce user anxiety regarding whether the meeting is actually being captured.

**Independent Test**: Mock a long-running transcription phase and assert the database correctly reflects a "transcribing" state rather than a broad "in-progress" state.

**Acceptance Scenarios**:

1. **Given** the orchestrator transitions between isolated tasks (e.g., from joining to recording), **When** the transition occurs, **Then** the core database immediately logs the precise new state of the pipeline (e.g. "joining", "recording", "transcribing", "completed").
2. **Given** a user opens the Frontend Dashboard during an active meeting, **When** they view the meeting history list, **Then** they see the live status indicator matching the exact pipeline progression securely.

---

### User Story 3 - Graceful Degradation & Server Protection (Priority: P2)

Users running the core platform backend expect that a single failing meeting bot will not crash the entire server causing every other active bot to fail simultaneously.

**Why this priority**: If joining Meeting A causes a fatal error that crashes the overarching web framework, Meetings B, C, and D are destroyed. The pipeline must contain its own failures.

**Independent Test**: Mock a catastrophic transcription API failure triggering an abort, and assert the system simply marks that specific meeting as `failed` while the host server remains perfectly active.

**Acceptance Scenarios**:

1. **Given** a critical fault occurs inside a specific module (e.g., the STT engine goes offline permanently), **When** the orchestrator catches the error, **Then** it cleanly aborts that specific pipeline, marks the meeting status as `failed` in the database, and logs the reason.
2. **Given** multiple meetings scheduled concurrently, **When** a pipeline executes heavily blocking visual rendering elements (Selenium) or recording bounds, **Then** the orchestrator guarantees these processes do not lock or freeze the overarching application server from accepting new web requests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST execute the pipeline as a detached background process ensuring the REST API endpoint allocating the request responds instantly to the frontend.
- **FR-002**: The system MUST synchronously step through logical boundaries: 1) Join 2) Record 3) Wait 4) Halt 5) Transcribe 6) Summarize 7) Dispatch.
- **FR-003**: The system MUST mutate the native system database strictly at every phase transition identifying active boundaries (`joining`, `recording`, etc).
- **FR-004**: The system MUST isolate slow, synchronous operations (like visual browser manipulation) into executing threads to avoid permanently freezing the native web framework.
- **FR-005**: The system MUST capture explicitly thrown downstream Module Exceptions (e.g., `TR-001` or `SM-002`) abandoning loops seamlessly without destroying broader processes.

### Key Entities

- **Orchestration Loop**: The sequential control flow managing the asynchronous handoffs between all major infrastructure modules natively.
- **State Tracker**: The direct database coupling reflecting active workflow boundaries in real-time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pipeline completely routes a valid execution flow utilizing mocked dependencies terminating with Database Storage within standard execution limits.
- **SC-002**: The active database `status` tracks sequentially parsing `joining` -> `recording` -> `transcribing` -> `summarising` -> `delivering` successfully displaying live progression natively.
- **SC-003**: Injections of forced exceptions (e.g., `BrowserCrash`) inside isolated pipelines successfully set the status tracking state to `failed` while the main server loops continue operating effortlessly.
