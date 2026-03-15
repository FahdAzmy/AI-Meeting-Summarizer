---
description: "Task list for Audio Capture Module feature implementation"
---

# Tasks: Audio Capture Module

**Input**: Design documents from `/specs/004-audio-capture/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Test-Driven Development (TDD) is governed heavily by the constitution. Every WebSocket connection via `obsws-python` MUST be structurally mocked using `unittest.mock` to prevent CI pipelines from attempting to boot an entire video production environment during code checks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Python module configuration and static payload preparation.

- [ ] T001 Ensure `obsws-python` dependency is added to the project's root `requirements.txt`.
- [ ] T002 Add `AudioCapture` specific connection configurations (host, port, password, output_dir) into the core `config/settings.py` structure.
- [ ] T003 Create custom exception models (AC-001 through AC-005) inside `modules/errors.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Build initial `AudioCapture` class scaffold with empty `__init__`, `start`, `stop`, and `healthcheck` declarations in `modules/audio_capture.py`.
- [ ] T005 [P] Setup base Pytest fixture that accurately mocks `obsws_python.ReqClient` structurally within `tests/unit/test_audio_capture.py`.

**Checkpoint**: Core module structure instantiated and test suite runs blindly against fake OBS sockets natively.

---

## Phase 3: User Story 1 - Predictable System Audio Capture (Priority: P1) 🎯 MVP

**Goal**: Successfully transmit and process the start and stop commands to a mocked rendering engine.

**Independent Test**: Assert that the Python module calls the exact downstream WebSocket string commands precisely when `start()` and `stop()` are triggered locally.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T006 [P] [US1] Unit test `__init__` asserting that `obsws_python.ReqClient` is instantiated using variables mapped from the Config in `tests/unit/test_audio_capture.py`
- [ ] T007 [P] [US1] Unit test `start()` asserting it calls `client.start_record()` over the mocked socket in `tests/unit/test_audio_capture.py`
- [ ] T008 [P] [US1] Unit test `stop()` asserting it calls `client.stop_record()` and parses the mock boolean output successfully in `tests/unit/test_audio_capture.py`

### Implementation for User Story 1

- [ ] T009 [US1] Implement `__init__` in `modules/audio_capture.py` applying `Config` credentials.
- [ ] T010 [US1] Implement `start()` routing execution strings down to the `ReqClient` in `modules/audio_capture.py`.
- [ ] T011 [US1] Implement `stop()` fetching and parsing the active payload paths returning the string file path down inside `modules/audio_capture.py`.

**Checkpoint**: The Python module bridges execution states dynamically over standard WebSockets.

---

## Phase 4: User Story 2 - Audio Integrity & Health Validation (Priority: P2)

**Goal**: Assert before runtime that the entire backend engine is healthy, reachable, and not disconnected.

**Independent Test**: Mock connection timeout responses and force the module to successfully digest and re-throw the custom `AC-0XX` error payloads.

### Tests for User Story 2  ⚠️

- [ ] T012 [P] [US2] Mock `healthcheck()` asserting it correctly polls `client.get_version()` and returns `True` logically in `tests/unit/test_audio_capture.py`
- [ ] T013 [P] [US2] Mock socket failure triggering `OBSConnectionError` correctly inside initialization blocks within `tests/unit/test_audio_capture.py`
- [ ] T014 [P] [US2] Assert that `start()` implicitly triggers and fails if `healthcheck()` is forced false within `tests/unit/test_audio_capture.py`

### Implementation for User Story 2

- [ ] T015 [US2] Implement `healthcheck()` resolving connection tests by throwing an arbitrary ping out the WebSocket inside `modules/audio_capture.py`
- [ ] T016 [US2] Refactor `__init__` and `healthcheck` to universally catch and specifically route errors as `OBSConnectionError` or `OBSNotRunning` explicitly in `modules/audio_capture.py`
- [ ] T017 [US2] Wrap file path directory writes asserting `Config.RECORDINGS_DIR` exists natively before executing writes in `modules/audio_capture.py`

**Checkpoint**: Application refuses to boot or join meetings without active microphone validations.

---

## Phase 5: User Story 3 - High-Fidelity Audio Delivery (Priority: P3)

**Goal**: Assure that the final recording payload output physically exists and operates as a non-silent corrupted file format.

**Independent Test**: Verify file pointers.

### Tests for User Story 3  ⚠️

- [ ] T018 [P] [US3] Unit test injecting a mock OS path check resolving a 0-byte file, ensuring `EmptyRecordingError` throws heavily in `tests/unit/test_audio_capture.py`

### Implementation for User Story 3

- [ ] T019 [US3] Finalize `stop()` by appending an `os.path.getsize()` check evaluating the returned WebSocket string, throwing `EmptyRecordingError` if bytes equal exactly `0` in `modules/audio_capture.py`

**Checkpoint**: The transcriber engine is guaranteed to never receive silent static payloads.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T020 Insert `logger.info` and `logger.error` traces specifically tracking payload durations and engine version connections universally across `modules/audio_capture.py`
- [ ] T021 Execute all pytest mocks and verify coverage guarantees 100% execution on module blocks without any active OBS instances.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Must occur immediately to define configurations and Exception models.
- **Foundational (Phase 2)**: Depends directly on Setup completion to resolve module scaffolding structurally.
- **User Stories (Phase 3+)**: Setup and Foundational block progressing into any OBS tests. Following Foundational, stories should progress in linear order (US1 → US2 → US3) since `start()` and `stop()` logic naturally requires connection validations built in US2.
- **Polish (Final Phase)**: Adds observability logging natively.

### Parallel Opportunities

- Tests within the same Phase / User Story can be engineered and executed simultaneously utilizing mocked connections.
- Creating the `errors.py` (AC-0XX schemas) is perfectly parallelizable alongside editing the `config.py` blocks.

### Implementation Strategy

#### MVP First (User Story 1 Only)
1. Complete Phase 1 and 2 ensuring pytest properly blocks external socket calls natively.
2. Develop the socket communication bindings for `start()` and `stop()`.
3. Halt here and prototype locally utilizing `test_live_audio.py` against a real OBS Studio application to ensure binding accuracy. 

#### Incremental Delivery
- Once the prototype physically commands OBS successfully, layer in the aggressive healthchecks defined in User Story 2.
- Finalize by injecting the file system constraints defined within User Story 3 confirming data flow.
