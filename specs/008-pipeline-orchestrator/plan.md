# Implementation Plan: Pipeline Orchestrator

**Branch**: `008-pipeline-orchestrator` | **Date**: 2026-03-15 | **Spec**: [specs/008-pipeline-orchestrator/spec.md](spec.md)
**Input**: Feature specification from `/specs/008-pipeline-orchestrator/spec.md`

## Summary

The Pipeline Orchestrator serves as the central nervous system of the AI Assistant. It bridges the REST API web framework natively to the internal intelligence array orchestrating `MeetingAccess`, `AudioCapture`, `Transcription`, `Summarisation`, and `OutputStorage` seamlessly. It ensures deep monitoring by updating database statuses directly (from "JOINING" to "DELIVERING") and executes natively as an isolated Background Task to prevent long-running AI constraints from negatively impacting or hanging the core FastAPI service.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `fastapi` (BackgroundTasks), `asyncio`, `beanie` (for real-time tracking)
**Storage**: MongoDB (Updating live Document instances)
**Testing**: `pytest`, `pytest-asyncio`, `unittest.mock` simulating explicit exceptions across modules validating the internal `try/except` abort loops.
**Target Platform**: Backend Python Environment.
**Project Type**: Backend Python Main Executable (`main.py` & orchestrator dependencies)
**Performance Goals**: Natively offloads all 60-minute duration tasks avoiding core framework hangs. State switches update in < 150ms.
**Constraints**: Must juggle concurrent pipelines effectively utilizing OS threading pools for blocking modules legitimately preventing thread-locks natively.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Test-Driven Development**: The orchestrator is simply an array of method calls spanning module layers. Pytest suites mock EVERY underlying module ensuring the orchestration routing correctly maps "Failure -> DB updates" organically. 
- [x] **II. High-Quality UI/UX Design**: *N/A (Backend logic block)*
- [x] **III. Async Processing & Performance Optimization**: Directly translates explicit limits pushing execution directly onto standard threading loops.
- [x] **IV. Modular & Extensible Architecture**: Because all individual components already adhere to explicit interfaces (`transcribe()`, `start()`, `send_email()`), the orchestrator is profoundly decoupled remaining totally independent of underlying implementations genuinely.
- [x] **V. Robust Observability & Error Handling**: Actively traps errors at every individual module stage routing them explicitly into standard database "Failed" tags mapping flawlessly back natively.

*Status: PASS*

## Project Structure

### Documentation (this feature)

```text
specs/008-pipeline-orchestrator/
├── plan.md              # This file
├── research.md          # Multi-threading and Event loops
├── data-model.md        # The sequential Status schema matching tracking models
├── quickstart.md        # Simulating endpoint POST routines
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
# Option 1: Single project - Specific to the Python Pipeline Service
├── src/   (or root modules dir)
│   ├── main.py                  # Endpoints initiating the orchestration
│   └── orchestrator.py          # The `run_pipeline` task runner
└── tests/
    └── unit/
        └── test_orchestrator.py # Pytest isolating the step progression arrays
```

**Structure Decision**: Integrated into Option 1 (Single Project root) specifically targeting the existing Python backend orchestrator folders.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None*    | *N/A*      | *N/A*                               |
