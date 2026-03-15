---
description: "Task list for Summarisation & Analysis Module feature implementation"
---

# Tasks: Summarisation & Analysis Module

**Input**: Design documents from `/specs/006-summarisation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Test-Driven Development (TDD) demands that we STRICTLY mock the OpenAI endpoints (`openai.OpenAI()` objects). We cannot write test cases that cost money or have non-deterministic API return outputs natively. All assertions test if our schemas parse correctly from mocked dicts.

**Organization**: Tasks are grouped by user story natively.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: External package initialization and standard error blueprints natively.

- [ ] T001 Pin `openai>=1.0` and `pydantic>=2.0` formally inside the root `requirements.txt` file.
- [ ] T002 Aggregate standard target keys (`OPENAI_API_KEY`, `LLM_MODEL`) actively loading from generic environment maps inside `config/settings.py`.
- [ ] T003 Construct the Exception architecture (`SM-001` through `SM-004`) mapping pipeline breaks explicitly inside `modules/llm_errors.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core logic scaffolding that MUST be instantiated before analysis begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Architect the base class `Summarisation` defining the constructor mapping the model tracker and locking `temperature` natively in `modules/summarisation.py`.
- [ ] T005 [P] Setup base Pytest suites mapping `unittest.mock.patch` over the `openai` Python SDK guaranteeing safe CI loops natively inside `tests/unit/test_summarisation.py`.

**Checkpoint**: Core framework executes safely refusing external web connections seamlessly.

---

## Phase 3: User Story 1 & 2 - Summaries and Action Extraction (Priority: P1) 🎯 MVP

**Goal**: Seamlessly wrap Transcript dicts driving them directly through OpenAI's JSON Mode parsing cleanly into Pydantic models verifying structure natively.

**Independent Test**: Simulate standard ChatGPT JSON string returns measuring whether the application correctly binds them to specific array indices.

### Tests for User Story 1 & 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T006 [P] [US1] Unit test `generate_report()` by injecting mocked OpenAI payload strings asserting the returned `summary` key physically exists handling markdown text in `tests/unit/test_summarisation.py`
- [ ] T007 [P] [US2] Mock the strict LLM JSON mapping isolating Action Items resolving exactly that assigning matrices load correctly to Py lists inside `tests/unit/test_summarisation.py`
- [ ] T008 [P] [US2] Feed an intentionally mangled missing-key mock string to specifically trigger and test the `ParseError` exceptions boundary checking natively in `tests/unit/test_summarisation.py`

### Implementation for User Story 1 & 2

- [ ] T009 [US1] Scaffold formal `Pydantic` mapping classes structurally mimicking the `MeetingReport` object boundaries ensuring strict static typing securely in `modules/summarisation.py`.
- [ ] T010 [US1] Construct standard `_generate_summary` prompts dynamically embedding the full transcription natively mapping to standard Chat completions logic enforcing JSON outputs in `modules/summarisation.py`.
- [ ] T011 [US2] Map the returned JSON dictionary executing extraction arrays specifically separating "Action Items", "Follow ups" and "Decisions" logic naturally inside `modules/summarisation.py`.

**Checkpoint**: Generative AI text reliably normalizes down to backend standard variables rather than arbitrary paragraphs.

---

## Phase 4: User Story 3 - Speaker Participation Analytics (Priority: P2)

**Goal**: Mathematically group diarized time clusters dynamically ranking the most communicative speaker directly.

**Independent Test**: Measure integer counts accurately bypassing LLM layers completely mapping logic.

### Tests for User Story 3  ⚠️

- [ ] T012 [P] [US3] Supply predefined mock segments simulating math bounds verifying explicit duration totals load correctly into `tests/unit/test_summarisation.py`
- [ ] T013 [P] [US3] Unit test a simulated file completely omitting Diarization tags verifying the code gracefully exits computing the struct as `None` natively in `tests/unit/test_summarisation.py`

### Implementation for User Story 3

- [ ] T014 [US3] Construct `_analyse_participation(segments)` iterating explicitly over native data dicts executing grouping checks measuring seconds inherently within `modules/summarisation.py`.

**Checkpoint**: Participation data bridges perfectly adding extreme value beyond generic summaries efficiently.

---

## Phase 5: User Story 4 - Resiliency & Threshold Checking (Priority: P2)

**Goal**: Aggressively block non-standard boundaries actively optimizing latency windows stopping unnecessary execution naturally.

**Independent Test**: Mock explicit timeouts simulating API limits dropping correctly natively.

### Tests for User Story 4  ⚠️

- [ ] T015 [P] [US4] Mock a 0-byte transcript explicitly verifying `EmptyTranscriptError` triggers immediately returning 100% latency natively in `tests/unit/test_summarisation.py`
- [ ] T016 [P] [US4] Unit test an `HttpTimeoutError` from the mock OpenAI library mapping perfectly onto `LLMTimeoutError` effectively inside `tests/unit/test_summarisation.py`

### Implementation for User Story 4

- [ ] T017 [US4] Lock explicit bounds directly wrapping OpenAI's initialization call assigning `temperature=0.3` forcefully reducing creative drifts completely in `modules/summarisation.py`.
- [ ] T018 [US4] Implement a fast-exit `if not transcript["full_text"]` bounding check dropping standard `EmptyTranscriptError` avoiding any cost allocations structurally inside `modules/summarisation.py`.

**Checkpoint**: LLM execution perfectly restricted and isolated dynamically.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Assemble final orchestration controllers natively spanning broader logic execution efficiently.

- [ ] T019 Engineer the top-level orchestrator `generate_report(transcript)` binding all internal mathematics bridging natively via mapping correctly inside `modules/summarisation.py`.
- [ ] T020 Deploy explicit `logger.info()` boundaries measuring explicit LLM execution limits calculating response delivery tracking native API bounds implicitly inside `modules/summarisation.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Base logic dependencies map completely first natively.
- **Foundational (Phase 2)**: Class construction handles foundational configurations blocking subsequent API payloads natively.
- **User Stories (Phase 3 & 4)**: The extraction prompt engineering executes natively utilizing JSON modeling boundaries mapping structs efficiently. Speaker math runs orthogonally parallel not requiring LLM paths naturally.
- **Polish (Final Phase)**: Global orchestration combines strings and math objects dynamically into the final payload payload matrix.

### Parallel Opportunities

- Engineers can safely split constructing analytical math algorithms explicitly targeting speaker lengths alongside Developers mapping the native JSON extraction blocks from OpenAI payloads independently.
- Constructing exception wrapper models runs effortlessly alongside module scaffolding implicitly.

### Implementation Strategy

#### MVP First (User Story 1 & 2)
1. Build out Setup explicitly parsing Pydantic and environments natively.
2. Draft the precise execution prompts explicitly feeding mocked transcript buffers wrapping logic properly avoiding math boundaries.
3. Validate Pydantic successfully parses OpenAI's explicit JSON payload schema reliably returning standard python arrays seamlessly.

#### Incremental Delivery
- Hook logic generating native dictionaries measuring duration limits independently validating arrays completely structurally.
- Finish explicitly bridging mathematical results dynamically back onto the overarching `MeetingReport` object.
