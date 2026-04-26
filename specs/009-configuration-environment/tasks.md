# Tasks: Configuration & Environment Management

**Input**: Design documents from `/specs/009-configuration-environment/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included as part of TDD methodology per project Constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create `.env.example` in repo root with placeholder values for all configurable fields (FR-013)
- [ ] T002 [P] Create `tests/unit/test_settings.py` scaffolding
- [ ] T003 Create `backend/models/settings_override.py` scaffolding

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Refactor `backend/config/settings.py` to remove direct instance instantiation (`config = Config()`) and prepare for dynamic async resolution
- [ ] T005 [P] Set up dependency injection for settings in FastAPI app (e.g., generic `Depends(get_settings)`)

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order

---

## Phase 3: User Story 1 - Centralized Settings Access (Priority: P1) 🎯 MVP

**Goal**: All application settings are declared and validated in a single, central location.

**Independent Test**: Can be fully tested by instantiating the configuration object and verifying that all domains (Server, MongoDB, STT, LLM, OBS, Email, Sheets) have the expected defaults.

### Implementation for User Story 1

- [ ] T006 [P] [US1] Add unit tests for `Config` initialization and default values in `tests/unit/test_settings.py`
- [ ] T007 [US1] Define all configuration fields in `Config` model in `backend/config/settings.py` with appropriate types and default values (FR-001, FR-003, FR-008)
- [ ] T008 [US1] Implement validation logic to ensure types, ranges, and formats are correct (FR-002, FR-007)
- [ ] T009 [US1] Add logic to auto-create required output directories (`RECORDINGS_DIR`, `TRANSCRIPTS_DIR`, `SUMMARIES_DIR`, `LOGS_DIR`) during initialization (FR-012)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Environment-Based Configuration (Priority: P1)

**Goal**: Configuration values are loadable from environment variables and a local environment file.

**Independent Test**: Can be tested by setting environment variables and providing a `.env` file, verifying values are correctly loaded.

### Implementation for User Story 2

- [ ] T010 [P] [US2] Add unit tests for environment variable overrides and `.env` loading in `tests/unit/test_settings.py`
- [ ] T011 [US2] Configure Pydantic `model_config` in `backend/config/settings.py` to load from `.env` file and ignore extra fields (FR-004, FR-005)
- [ ] T012 [US2] Ensure environment variable precedence over `.env` works automatically via Pydantic

**Checkpoint**: User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 & 4 - Dashboard Settings Override & Hierarchy (Priority: P2)

**Goal**: Runtime overrides from database with strict hierarchy (Defaults → .env → EnvVars → Dashboard).

**Independent Test**: Defining setting at all layers and verifying the correct override order; testing graceful fallback when DB is unreachable.

### Implementation for User Story 3 & 4

- [ ] T013 [P] [US3] Add unit tests for `get_settings` hierarchical resolution and DB fallback in `tests/unit/test_settings.py`
- [ ] T014 [US3] Create `SettingsOverride` Beanie Document model in `backend/models/settings_override.py` (fields: `stt_provider`, `storage_backend`, `email_sender`, `email_password`)
- [ ] T015 [US4] Implement async `get_settings()` in `backend/config/settings.py` to retrieve overrides from MongoDB and merge with Pydantic `Config`
- [ ] T016 [US4] Add robust error handling in `get_settings()` to gracefully fall back to base configuration if MongoDB is unreachable (FR-011)

**Checkpoint**: Overrides and hierarchy are functional.

---

## Phase 6: User Story 5 - Secrets Protection & Degraded Mode (Priority: P2)

**Goal**: Mask sensitive logs and gracefully handle missing active provider keys without crashing the app server.

**Independent Test**: Missing active provider key blocks pipeline but UI remains accessible; logs do not contain raw passwords or API keys.

### Implementation for User Story 5

- [ ] T017 [P] [US5] Add unit tests for secret masking and degraded mode behavior in `tests/unit/test_settings.py`
- [ ] T018 [US5] Add `model_dump()` override or custom formatting property in `Config` (`backend/config/settings.py`) to mask fields containing 'KEY' or 'PASSWORD' with `***` (FR-009)
- [ ] T019 [US5] Implement degraded mode validation in `get_settings()` to catch missing active provider keys and set an internal `_is_degraded` flag rather than raising an unhandled exception (FR-014)
- [ ] T020 [US5] Expose degraded mode status so the frontend dashboard can alert the user

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and system integration.

- [ ] T021 [P] Update `backend/main.py` and routers to inject `get_settings` rather than importing global `config`
- [ ] T022 Code cleanup, typings verification, and refactoring
- [ ] T023 Run quickstart.md validation to ensure new developers can onboard correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Stories (Phase 3+)**: Must start chronologically (Phase 3 → Phase 4 → Phase 5 → Phase 6) due to iterative expansion of the configuration object.
- **Polish (Final Phase)**: Depends on all user stories being complete

### Parallel Opportunities

- Unit tests across all phases (T002, T006, T010, T013, T017) can be scaffolded or written in parallel.
- `SettingsOverride` DB model (T014) can be developed in parallel with Pydantic base configuration (Phase 3/4).

## Implementation Strategy

### MVP First (User Story 1 & 2)

1. Complete Setup + Foundational (T001-T005)
2. Complete US1 & US2 (Base Settings + Env overrides) (T006-T012)
3. **STOP and VALIDATE**: Test backend starts and correctly reads `.env` variables using type checking.

### Incremental Delivery

1. Deliver MVP (US1 + US2).
2. Add Database Overrides (US3 + US4) allowing frontend to toggle settings.
3. Add Security & Resilience (US5) to protect credentials and handle missing keys via degraded mode gracefully.
