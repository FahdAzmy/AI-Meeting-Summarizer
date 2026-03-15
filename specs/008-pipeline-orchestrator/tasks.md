---
description: "Task list for Pipeline Orchestrator feature implementation"
---

# Tasks: Pipeline Orchestrator

**Input**: Design documents from `/specs/008-pipeline-orchestrator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Test-Driven Development (TDD) strictly demands that NO underlying modules actually execute. All tests must rely heavily on `unittest.mock.patch` wrapping `MeetingAccess`, `AudioCapture`, `Transcription`, `Summarisation`, and `OutputStorage`. We are simply testing the *routing logic* and `MeetingStatus` database mutations!

**Organization**: Tasks are grouped by user story logically bridging execution steps natively.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffolding base configurations verifying FastAPI environment bridges natively cleanly.

- [ ] T001 Ensure `fastapi`, `uvicorn`, `beanie`, and `pytest-asyncio` are formally pinned within the root `requirements.txt`.
- [ ] T002 Aggregate the application `MeetingStatus` enumeration mapping `JOINING`, `RECORDING`, `TRANSCRIBING`, `SUMMARISING`, `DELIVERING`, `COMPLETED`, and `FAILED` completely within `src/models/meeting.py` (or equivalent data model registry).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Creating the actual isolated execution frameworks verifying native test boundaries.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Scaffold the core `run_pipeline(meeting_link, emails, storage)` asynchronous function definition structurally avoiding imports natively within `src/orchestrator.py`.
- [ ] T004 [P] Setup the base Pytest harness natively deploying `@pytest.mark.asyncio` and isolating mocked driver databases successfully within `tests/unit/test_orchestrator.py`.

**Checkpoint**: Development environment safely isolates tests preventing active network executions.

---

## Phase 3: User Story 1 - Frictionless End-to-End Automation (Priority: P1) 🎯 MVP

**Goal**: Sequentially instantiate and invoke every AI module dynamically passing data attributes structurally across bounds.

**Independent Test**: Mock every specific module class confirming the call count registers exactly `1` for each natively spanning the `try` block.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [P] [US1] Inject extensive standard `patch` decorators simulating the 5 core AI module classes validating sequential execution cleanly natively inside `tests/unit/test_orchestrator.py`
- [ ] T006 [P] [US1] Unit test data handover specifically measuring if the output of `transcribe()` maps perfectly into `generate_report()` natively without dropping dictionaries inside `tests/unit/test_orchestrator.py`

### Implementation for User Story 1

- [ ] T007 [US1] Build out the core `run_pipeline` function organically instantiating `MeetingAccess`, `AudioCapture`, `Transcription`, `Summarisation`, and `OutputStorage` explicitly inside `src/orchestrator.py`.
- [ ] T008 [US1] Link output bindings correctly mapping the transcript dict mapping directly natively into the LLM structurally passing `MeetingReport` models natively to storage bounds inside `src/orchestrator.py`.

**Checkpoint**: A complete simulated meeting flows from execution launch directly to physical SMTP logic completely functionally.

---

## Phase 4: User Story 2 - Real-Time Dashboard Visibility (Priority: P1) 🎯 MVP

**Goal**: Interleave active `Beanie` database mutation calls logically representing physical boundary boundaries updating UI hooks effortlessly.

**Independent Test**: Assert that the mock `Meeting.save()` function was called sequentially matching exactly the expected status parameters cleanly.

### Tests for User Story 2  ⚠️

- [ ] T009 [P] [US2] Mock the Beanie `Meeting` database object evaluating specifically that `.status` tracks from `JOINING` structurally down into `COMPLETED` cleanly over execution structurally natively in `tests/unit/test_orchestrator.py`
- [ ] T010 [P] [US2] Unit test an asynchronous database `.insert()` call physically deploying standard session schemas structurally before the loop actually begins dynamically inside `tests/unit/test_orchestrator.py`

### Implementation for User Story 2

- [ ] T011 [US2] Interleave hard `meeting.status = ...` assignment blocks dynamically checking boundary phases logically running `await meeting.save()` explicitly mapping inside `src/orchestrator.py`.

**Checkpoint**: The active UI safely reflects processing states dynamically avoiding black box assumptions natively.

---

## Phase 5: User Story 3 - Graceful Degradation & Protection (Priority: P2)

**Goal**: Protect the FastAPI web engine from freezing utilizing `asyncio.to_thread`. Wrap the entire pipeline dynamically safely tracking internal `Exceptions`.

**Independent Test**: Inject a fake unhandled Exception (e.g. `KeyboardInterrupt`) tracking if the orchestration correctly labels it `FAILED` structurally without escaping up to standard REST logs explicitly.

### Tests for User Story 5 ⚠️

- [ ] T012 [P] [US3] Mock `transcribe()` explicitly throwing an `Exception` verifying the Orchestrator inherently traps it mathematically natively assigning `FAILED` within `tests/unit/test_orchestrator.py`
- [ ] T013 [P] [US3] Extract standard tracking loops validating `asyncio.to_thread` natively launches `MeetingAccess.join` perfectly avoiding single-threading stalls within `tests/unit/test_orchestrator.py`

### Implementation for User Story 5

- [ ] T014 [US3] Force `asyncio.to_thread()` execution bindings dynamically isolating `access.join()` and `capture.start()` natively detaching logic structurally avoiding REST blocks natively inside `src/orchestrator.py`.
- [ ] T015 [US3] Architect overarching `try/except Exception` bounds inherently logging critical traces structurally reverting native Database `Meeting.status` structurally evaluating failures perfectly inside `src/orchestrator.py`.

**Checkpoint**: One failing robot natively saves logs without halting core server delivery parameters.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Stitch the pipeline orchestrator perfectly to standard API `BackgroundTasks` directly allocating physical endpoints flawlessly.

- [ ] T016 Register standard REST POST routing configurations simulating `uvicorn` deploying FastAPI endpoints (`/trigger` mapped dynamically) accurately within `src/main.py`.
- [ ] T017 Execute explicit bindings linking `/trigger` to FastAPI's `BackgroundTasks.add_task(run_pipeline, ...)` specifically proving endpoint decoupling functionally inside `src/main.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: The Database Enum trackers must logically exist mapping bounds.
- **Foundational (Phase 2)**: Core task runners instantiated.
- **User Stories (Phase 3, 4, 5)**: The flow structurally handles sequence creation, then interleaves database saves logically inside, before executing dynamic Thread pools isolating blocking paths structurally.
- **Polish (Final Phase)**: Global routing ensures external Frontends map triggers correctly launching the module boundaries cleanly.

### Parallel Opportunities

- Testing loops generating state trackers naturally avoids blocking engineering loops bridging HTTP endpoints fundamentally safely natively.
- Generating the FastAPI `BackgroundTasks` endpoint structurally works entirely independent of specific AI module linkages dynamically validating structural bounds cleanly.

### Implementation Strategy

#### MVP First (User Story 1 & 2)
1. Instantiate the Python sequence mapped dynamically evaluating standard loops reliably returning states across modules.
2. Bind the DB logic injecting standard MongoDB checks evaluating `COMPLETED` effectively tracking natively structurally.

#### Incremental Delivery
- Force threading validations measuring native FastAPI blocks successfully escaping single-threaded ecosystems natively seamlessly.
- Expose the HTTP API bindings utilizing standard web framework mapping securely handling incoming web parameters.
