---
description: "Task list for Transcription Module feature implementation"
---

# Tasks: Transcription Module

**Input**: Design documents from `/specs/005-transcription/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Test-Driven Development (TDD) dictates that no real API requests should be sent to OpenAI, Deepgram, or AssemblyAI during automated checks. ALL HTTP outputs must be bypassed via mocked testing libraries (such as `responses` or `unittest.mock`).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Python dependency inclusions and fundamental structures natively.

- [X] T001 Inject `openai`, `deepgram-sdk`, `assemblyai`, and `requests` mapping directly into the root `requirements.txt` file.
- [X] T002 Aggregate the STT API Key structs (`WHISPER_API_KEY`, etc.) inside environment namespaces and expose them natively via `config/settings.py`.
- [X] T003 Construct the Exception structs (TR-001 through TR-005) inheriting from Python base `Exception` cleanly inside `modules/stt_errors.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY STT routing interactions can happen.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Blueprint the empty `Transcription` router class handling `__init__(provider="whisper")` mapping the respective config API keys in `modules/transcription.py`.
- [X] T005 [P] Setup base `pytest` fixtures asserting explicit isolation via `mock` preventing live environment credentials leaking within `tests/unit/test_transcription.py`.

**Checkpoint**: Application boots natively and testing configurations run cleanly without active payloads. ✅

---

## Phase 3: User Story 1 - Unified Audio Transcription (Priority: P1) 🎯 MVP

**Goal**: Guarantee standardized JSON processing regardless of downstream target providers.

**Independent Test**: Simulate varying raw API outputs correctly parsing back as the normalized `TranscriptResult`.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T006 [P] [US1] Unit test `_transcribe_whisper` by asserting `mock` intercepts the OpenAI client explicitly returning simulated output in `tests/unit/test_transcription.py`
- [X] T007 [P] [US1] Unit test `_transcribe_deepgram` returning simulated diarization JSON outputs securely isolating the SDK inside `tests/unit/test_transcription.py`
- [X] T008 [P] [US1] Unit test `_transcribe_assemblyai` mirroring standard responses within `tests/unit/test_transcription.py`
- [X] T009 [P] [US1] Assert precisely that `_normalise` digests all three mock variants actively transforming them mathematically identically down to the `TranscriptResult` object inside `tests/unit/test_transcription.py`

### Implementation for User Story 1

- [X] T010 [US1] Structure OpenAI's Python object SDK mapped specifically through `_transcribe_whisper` natively executing uploads logically in `modules/transcription.py`.
- [X] T011 [US1] Construct the `_transcribe_deepgram` payload method asserting proper URL HTTP requests explicitly demanding "diarize=true" in `modules/transcription.py`.
- [X] T012 [US1] Scaffold the explicit async polling behaviors via `_transcribe_assemblyai` actively resolving audio results in `modules/transcription.py`.
- [X] T013 [US1] Engineer the `_normalise` helper bridging specific raw variables into `TranscriptResult` boundaries directly inside `modules/transcription.py`.

**Checkpoint**: The Python orchestrator natively standardizes multi-provider data structures effectively. ✅

---

## Phase 4: User Story 2 - Resilient Provider Routing & Fallbacks (Priority: P2)

**Goal**: Seamlessly survive network timeouts bypassing `HTTP 408` or target alternative frameworks gracefully during `HTTP 429` locks.

**Independent Test**: Mock explicit server faults confirming the orchestrator natively routes properly over time barriers.

### Tests for User Story 2  ⚠️

- [X] T014 [P] [US2] Mock explicit 408 Requests Timeouts verifying the orchestrator delays sequentially (`sleep`) 3 attempts before raising `STTTimeoutError` inside `tests/unit/test_transcription.py`
- [X] T015 [P] [US2] Assert exactly that pushing a simulated `HTTP 429` status flag triggers the top level `provider` switch actively targeting the secondary fallback natively in `tests/unit/test_transcription.py`
- [X] T016 [P] [US2] Mock an `HTTP 401 Unauthorized` check asserting an instant pipeline dropout without backoff triggering cleanly in `tests/unit/test_transcription.py`

### Implementation for User Story 2

- [X] T017 [US2] Engineer a dynamic retry loop executing exponential scaling timeouts securely tracking attempt bounds actively prior to API executions natively in `modules/transcription.py`.
- [X] T018 [US2] Finalize the `transcribe(audio_path)` controller explicitly mapping the core Engine Router checking dynamically against 429 API responses and swapping standard methods implicitly in `modules/transcription.py`.

**Checkpoint**: Transcription process maintains robust resiliency despite volatile web circumstances. ✅

---

## Phase 5: User Story 3 - Graceful File Size Management (Priority: P3)

**Goal**: Intercept large meeting files failing efficiently rather than spamming unresolvable STT APIs globally.

**Independent Test**: Mock oversized byte counts confirming immediate errors trigger natively.

### Tests for User Story 3  ⚠️

- [X] T019 [P] [US3] Override `os.path.getsize` via mock injecting `26000000` bytes (26MB) natively guaranteeing `AudioTooLargeError` triggers independently inside `tests/unit/test_transcription.py`

### Implementation for User Story 3

- [X] T020 [US3] Instantiate `os.path.getsize(audio_path)` tracking immediately at the top of the `transcribe()` block securely throwing `AudioTooLargeError` natively against thresholds exceeding 25MB limits natively in `modules/transcription.py`.

**Checkpoint**: File structures successfully assert parameter constraints inherently saving orchestrator upload overheads. ✅

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories natively.

- [X] T021 Incorporate explicit logic tracking execution metric latencies cleanly attaching `logger.info()` boundaries spanning exact payload responses effectively inside `modules/transcription.py`.
- [X] T022 Assert strict Python type hinting maps explicitly matching `data-model.md` structs inherently preventing downstream data bleeding accurately.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Base credentials loading executes first.
- **Foundational (Phase 2)**: Class construction handles foundational configurations blocking subsequent API payloads natively.
- **User Stories (Phase 3+)**: Setup and Foundational block progressing immediately mapped directly into User Story 1 (Standard API Requests). User Story 2 builds the active fault wrapper wrapping the original US1 methods seamlessly. User Story 3 enforces file guards directly at runtime invocation.
- **Polish (Final Phase)**: Final code telemetry tracking limits injected dynamically.

### Parallel Opportunities

- Engineers can safely fragment constructing individual API mappings cleanly (One Developer actively handles `_transcribe_deepgram` simultaneously alongside another Developer actively targeting `_transcribe_assemblyai` structurally).
- Constructing exception loops (`TR-0XX`) runs fully parallel externally isolated from the module's core orchestrator natively.

### Implementation Strategy

#### MVP First (User Story 1 Only)
1. Build out Setup explicitly parsing environment dependencies securely.
2. Formally generate mocked output payloads mapping perfectly onto `Whisper` structurally handling a singular explicit translation target path avoiding fallbacks natively.
3. Assert that regardless of native API dictionary outputs, `_normalise()` successfully guarantees the result maps explicitly to identical Data Models avoiding downstream pipeline failure mapping structurally. 

#### Incremental Delivery
- Once OpenAI mapping concludes cleanly, inject resilient network decorator boundaries guaranteeing the loop explicitly manages `requests` faults actively (User Story 2).
- Inject File Threshold validators preventing large `wav` leaks completely spanning pipeline boundaries seamlessly (User Story 3).
