---
description: "Task list for Meeting Access Module feature implementation"
---

# Tasks: Meeting Access Module

**Input**: Design documents from `/specs/003-meeting-access/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Test-Driven Development (TDD) is explicitly enforced in this project's constitution. All Selenium actions must be decoupled and tested via `unittest.mock` to ensure speedy CI runs without needing graphical headless execution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Python module configuration and static payload preparation.

- [x] T001 Initialize empty JSON config for selectors matching `data-model.md` inside `config/selectors.json`
- [x] T002 Create custom exception models (MA-001 through MA-004) inside `modules/errors.py`
- [x] T003 Ensure `webdriver-manager` and `selenium` exist in overarching `requirements.txt` (or pip install them to base environment)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Build initial `MeetingAccess` class scaffold with empty `__init__`, `join`, `wait_until_end`, and `leave` attributes in `modules/meeting_access.py`
- [x] T005 [P] Setup base Pytest fixture that mocks `selenium.webdriver.Chrome` universally within `tests/unit/test_meeting_access.py`

**Checkpoint**: Core module structure instantiated and test suite runs without opening Chrome.

---

## Phase 3: User Story 1 - Join Supported Meetings Automatically (Priority: P1) 🎯 MVP

**Goal**: Navigate accurately to Google Meet, Zoom, or Teams sessions bypassing pre-join friction automatically.

**Independent Test**: Supply valid mocked meeting URLs and verify the class appropriately routes execution patterns to particular platform sequences.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T006 [P] [US1] Unit test `_detect_platform` correctly parses valid and invalid URLs in `tests/unit/test_meeting_access.py`
- [x] T007 [P] [US1] Unit test `__init__` injects required `--use-fake-ui-for-media-stream` and fake device browser flags in `tests/unit/test_meeting_access.py`
- [x] T008 [P] [US1] Mock explicit wait logic & interaction sequences for the Google Meet path in `tests/unit/test_meeting_access.py`
- [x] T009 [P] [US1] Mock explicit wait logic & display name text-sending targeting the Zoom path in `tests/unit/test_meeting_access.py`
- [x] T010 [P] [US1] Mock explicit wait logic & iframe/button interactions targeting the MS Teams path in `tests/unit/test_meeting_access.py`

### Implementation for User Story 1

- [x] T011 [US1] Implement `_detect_platform` utilizing regex or string checking in `modules/meeting_access.py`
- [x] T012 [US1] Implement `__init__` bootstrapping the headless driver securely via Config options in `modules/meeting_access.py`
- [x] T013 [US1] Ingest `config/selectors.json` payload during instantiation enabling dynamic interaction handles in `modules/meeting_access.py`
- [x] T014 [US1] Develop the `join(link)` router function switching between dedicated platform methods based on detection variables in `modules/meeting_access.py`
- [x] T015 [US1] Implement Google Meet join logic (Dismiss, Mute Mic/Cam, "Join Now") in `modules/meeting_access.py`
- [x] T016 [US1] Implement Zoom join logic (Enter Name, Join, parse Waiting Room visibility) in `modules/meeting_access.py`
- [x] T017 [US1] Implement MS Teams join logic (Bypass app prompt, select browser, Mute, Join) in `modules/meeting_access.py`

**Checkpoint**: The active bot can connect to the core supported suites successfully in isolation.

---

## Phase 4: User Story 2 - Autonomous Meeting End Detection (Priority: P2)

**Goal**: Detect when the meeting is over using periodic DOM polling.

**Independent Test**: Mock Selenium finding the specific "Meeting Ended" tags and ensure `wait_until_end` unblocks execution seamlessly.

### Tests for User Story 2  ⚠️

- [x] T018 [P] [US2] Mock timer/polling loop that throws an exit sequence when returning true for an End Screen element inside `tests/unit/test_meeting_access.py`
- [x] T019 [P] [US2] Unit test ensuring `leave()` triggers `driver.quit()` precisely in `tests/unit/test_meeting_access.py`

### Implementation for User Story 2

- [x] T020 [US2] Implement `wait_until_end` with a 30-second `time.sleep` loop scanning the DOM for "Meeting Ended" elements inside `modules/meeting_access.py`
- [x] T021 [US2] Enhance end detection capturing Google tracking attributes (e.g. `data-call-ended`) in `modules/meeting_access.py`
- [x] T022 [US2] Enhance end detection processing Zoom disconnect dialogs and URL changes in `modules/meeting_access.py`
- [x] T023 [US2] Implement `leave()` method verifying explicit browser garbage collection and process termination in `modules/meeting_access.py`

**Checkpoint**: Bot exits instances politely and releases memory overhead automatically.

---

## Phase 5: User Story 3 - Comprehensive Failure Notifications (Priority: P3)

**Goal**: Recognize errors (waiting room lockouts, bad URLs, DOM changes) and throw appropriate exceptions to trigger main pipeline fallback emails.

**Independent Test**: Introduce mock faults simulating UI layout breaks and ensure the correct custom `Exception` payload is passed to the orchestrator layer without hanging infinitely.

### Tests for User Story 3  ⚠️

- [x] T024 [P] [US3] Mock `NoSuchElementException` firing consistently to test inner retry loop bounds (3 attempts) in `tests/unit/test_meeting_access.py`
- [x] T025 [P] [US3] Assert exactly `MeetingJoinError` raises after loops exhaust in `tests/unit/test_meeting_access.py`

### Implementation for User Story 3

- [x] T026 [US3] Encapsulate `join` sequences within a standardized retry block executing three attempts containing 10-second wait buffers in `modules/meeting_access.py`
- [x] T027 [US3] Refactor explicit wait failures inside the loop into logging alerts tracking attempt numbers in `modules/meeting_access.py`
- [x] T028 [US3] Throw `WaitingRoomTimeout` specifically if Host timeout conditions exceed limits globally within Zoom loops inside `modules/meeting_access.py`
- [x] T029 [US3] Implement immediate un-looped failure responses throwing `PlatformNotSupported` before webdriver instantiation in `modules/meeting_access.py`

**Checkpoint**: Bad connections and timeouts throw explicitly routed errors rather than leaving zombies.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [x] T030 Refactor simple class checks with Selenium explicit definitions (`WebDriverWait(driver, 10).until(...)`) across all interaction paths instead of manual generic sleeps.
- [x] T031 Inject explicit logging statements `logger.info`, `logger.debug` around step transitions.
- [x] T032 Verify comprehensive output from Pytest across all permutations cleanly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can begin instantly.
- **Foundational (Phase 2)**: Depends directly on Setup completion to provide access to custom exceptions and payloads.
- **User Stories (Phase 3+)**: Setup and Foundational block progressing into any Selenium mock tests or routing. All tests must be executed initially.
- **Polish (Final Phase)**: Replaces sleep loops and augments with production-grade elements.

### Parallel Opportunities

- The creation of `selectors.json` and custom Exception models can be done by multiple developers completely disjoint from the actual Python testing structure.
- While mocking the interface tests (T006 - T010), developers can parallelize the mock workflows across different feature environments (Google Meet tests built separately from Teams mock tests).

### Implementation Strategy

#### MVP First (User Story 1 Only)
1. Complete Phase 1 and 2 (Basic classes, Exceptions).
2. Write tests simulating a single meeting link type connecting sequentially.
3. Build the backend code passing those unit tests safely locally.
4. Scale outward extending the pattern across other supported configurations.

#### Incremental Delivery
- Following US1 completion, integrate the `wait_until_end` logic guaranteeing resources are not leaked after a single test.
- Final wrap introduces the exception paths assuring the process doesn't infinitely hang when provided garbage links or waiting long periods for hosts.
