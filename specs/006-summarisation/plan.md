# Implementation Plan: Summarisation & Analysis Module

**Branch**: `006-summarisation` | **Date**: 2026-03-15 | **Spec**: [specs/006-summarisation/spec.md](spec.md)
**Input**: Feature specification from `/specs/006-summarisation/spec.md`

## Summary

The Summarisation & Analysis Module sits at the end of the AI Assistant pipeline. It consumes the standardized `TranscriptResult` object produced by the Transcription module and uses a Large Language Model (defaulting to GPT-4) to extract a structured markdown summary, discrete decision arrays, and accountable action items. Additionally, it computes equitable speaker participation metrics logically when diarization is provided, aggregating everything into a clean `MeetingReport` payload.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `openai>=1.0` (for LLM), `pydantic>=2.0` (for strict JSON schema outputs from LLM calls)
**Storage**: N/A (Module receives a dict and returns a dict in memory)
**Testing**: `pytest`, `unittest.mock` to mock LLM completions avoiding expensive API calls.
**Target Platform**: Backend Python Environment.
**Project Type**: Backend Python Module (`summarisation.py`)
**Performance Goals**: LLM text generation and statistical math must comfortably complete under 120 seconds limit.
**Constraints**: Requires explicit connection details for the structured LLM output API.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Test-Driven Development**: All external OpenAI LLM completion endpoints are mocked rigorously to ensure extraction math can be unit-tested without costs.
- [x] **II. High-Quality UI/UX Design**: *N/A (Backend logic block)*
- [x] **III. Async Processing & Performance Optimization**: Modules are built sequentially in the pipeline but isolated per-meeting, preventing hanging the main threading system.
- [x] **IV. Modular & Extensible Architecture**: The prompt logic and LLM connection is decoupled, meaning swapping to Anthropic's Claude or local models only requires altering the `_generate_summary` proxy.
- [x] **V. Robust Observability & Error Handling**: Explicit error classifications (SM-001 through SM-004) gracefully abandon analysis if the API times out without crashing the overarching host.

*Status: PASS*

## Project Structure

### Documentation (this feature)

```text
specs/006-summarisation/
├── plan.md              # This file
├── research.md          # LLM JSON parsing strategies
├── data-model.md        # The MeetingReport output standard
├── quickstart.md        # Environment variables mapping for LLMs
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
# Option 1: Single project - Specific to the Python Pipeline Service
├── config/
│   └── settings.py              # Environment variables mapping
├── modules/
│   ├── __init__.py
│   ├── summarisation.py         # Main LLM Orchestrator
│   └── llm_errors.py            # Contains SM-0XX Exception models
└── tests/
    └── unit/
        └── test_summarisation.py # Pytest mocking LLM outputs
```

**Structure Decision**: Integrated into Option 1 (Single Project root) specifically targeting the existing Python backend orchestrator folders.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None*    | *N/A*      | *N/A*                               |
