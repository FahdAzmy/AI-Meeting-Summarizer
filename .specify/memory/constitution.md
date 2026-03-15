<!--
## Sync Impact Report
- **Version change**: 0.0.0 (template) → 1.0.0
- **Modified principles**: N/A (initial constitution)
- **Added sections**:
  - Core Principles (I–VI)
  - Technology & Architecture Constraints
  - Development Workflow
  - Governance
- **Removed sections**: All template placeholders replaced
- **Templates requiring updates**:
  - `.specify/templates/plan-template.md` — ✅ Constitution Check section already references constitution; no update needed
  - `.specify/templates/spec-template.md` — ✅ No constitution-specific references; compatible as-is
  - `.specify/templates/tasks-template.md` — ✅ TDD task ordering aligns with Principle III; compatible as-is
- **Follow-up TODOs**: None
-->

# AI-Powered Meeting Assistant Constitution

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

All production code MUST be preceded by a failing test that defines the expected behaviour. The **Red → Green → Refactor** cycle is strictly enforced for every module from SPEC-00 through SPEC-09.

- Tests are the **living specification** — they serve as executable documentation of system behaviour.
- No production code in `app.py`, `main.py`, `models.py`, `modules/*.py`, or `utils/*.py` may be written without a corresponding failing test first.
- Each module's test file MUST exist before the module implementation begins.
- Overall test coverage MUST be ≥ 80% line coverage; individual module targets are defined in the Specifications (SPEC-10).
- All external dependencies (APIs, SMTP, OBS WebSocket, Google Sheets) MUST be mocked in unit tests.
- Shared fixtures (`conftest.py`) MUST provide a Flask test client, in-memory test database, and reusable sample data.

**Rationale:** TDD catches bugs in Selenium selectors, API response parsing, and email formatting before integration. The test suite acts as a safety net during refactoring and provider switching.

### II. Modular Pipeline Architecture

The system follows a **sequential pipeline architecture** with clearly separated modules. Each module MUST be independently testable, independently upgradable, and communicate through well-defined interfaces.

- **Module boundaries are hard**: Meeting Access, Audio Capture, Transcription, Summarisation, and Output & Storage are isolated units.
- Every module class MUST expose a documented public interface as defined in the Specifications (SPEC-01 through SPEC-05).
- Data flows between modules using normalised, schema-defined dictionaries (e.g., `TranscriptResult`, `MeetingReport`).
- The Pipeline Orchestrator (`main.py`) is the **only** component that wires modules together; modules MUST NOT directly import or depend on each other.
- New modules or providers MUST be added without modifying existing module code (Open/Closed Principle).

**Rationale:** Modularity enables replacing STT providers, switching LLMs, or updating platform selectors without cascading changes. It also makes each module independently testable via mocking.

### III. Configuration-Driven Flexibility

All external service endpoints, credentials, feature toggles, and operational parameters MUST be configurable via environment variables (`.env`) and the Settings database table — never hardcoded.

- The `Config` class in `config.py` is the single source of truth for all configuration values.
- Settings precedence: `.env` defaults → overridden by → Settings table (user-configured via dashboard).
- CSS selectors for meeting platforms MUST be stored in a configuration file (`config/selectors.json`) for easy updates.
- All file paths (recordings, transcripts, summaries, logs) MUST be configurable.
- API keys and credentials MUST never appear in source code or logs.

**Rationale:** Meeting platform UIs change frequently; the system must adapt without code changes. Users must be able to switch STT providers and storage backends instantly via the dashboard.

### IV. Graceful Error Handling & Observability

Every module MUST define explicit error codes, handle failures gracefully, and provide structured logging at appropriate severity levels. The system MUST never crash silently.

- Each module defines its own error code namespace (MA-xxx, AC-xxx, TR-xxx, SM-xxx, OS-xxx) as specified in SPEC-01 through SPEC-09.
- Retry policies MUST be used for transient failures: exponential backoff for API timeouts, provider switching for rate limits.
- Fallback chains MUST exist: primary STT → alternative STT; Google Sheets failure → local CSV; LLM failure → basic extractive summary.
- Every meeting session MUST produce a structured JSON session log at `./logs/session_{session_id}.json`.
- Log format: `[{timestamp}] [{level}] [{module}] {message}` — using Python's `logging` module.
- Pipeline status MUST be tracked in the `Meeting` database record, updating at each step for real-time dashboard visibility.

**Rationale:** External API dependencies (OBS, STT, LLM, SMTP) are inherently unreliable. The system must degrade gracefully rather than fail completely, and operators must be able to diagnose issues from logs alone.

### V. Security & Data Privacy

Participant data, credentials, and meeting recordings MUST be handled securely. No sensitive information may be exposed in logs, error messages, or insecure storage.

- Participant emails MUST NOT appear in application logs (NFR7).
- API keys and passwords MUST be stored in `.env` files and loaded via `python-dotenv`; never committed to version control.
- Email sender passwords MUST be encrypted in production when stored in the Settings database table.
- Transcriptions and summaries MUST be stored in secure storage — protected database or authenticated Google Sheets (NFR8).
- Audio recordings SHOULD be auto-cleaned after successful processing and storage.

**Rationale:** The system processes potentially sensitive meeting content. Privacy and security are non-negotiable for user trust and compliance.

### VI. Simplicity & YAGNI

Start with the simplest solution that satisfies the requirements. Do not over-engineer. Complexity MUST be justified and documented.

- The system supports **sequential** meeting processing (NFR9) — concurrent processing SHOULD NOT be implemented until explicitly required.
- The web dashboard uses Flask + Jinja2 templates — a single-page application framework MUST NOT be adopted unless explicitly decided.
- Storage backends are limited to SQLite/PostgreSQL and Google Sheets — additional backends MUST NOT be added without formal requirement.
- Single-user mode is the default — authentication and multi-user support are future enhancements, not current scope.
- If a simpler approach exists that meets the requirement, it MUST be preferred over a more complex one.

**Rationale:** This is a graduation project with fixed scope and timeline. Over-engineering consumes time better spent on core functionality and testing.

## Technology & Architecture Constraints

- **Language**: Python 3.10+ — all modules, utilities, and tests.
- **Web Framework**: Flask 3.x with Jinja2 templates, Flask-SQLAlchemy for ORM.
- **Browser Automation**: Selenium WebDriver with `webdriver-manager` for automatic driver management.
- **Audio Recording**: OBS Studio controlled via `obsws-python` WebSocket client.
- **STT Providers**: Whisper API (primary), Deepgram (alternative), AssemblyAI (alternative) — all behind a unified `Transcription` interface.
- **LLM Summarisation**: OpenAI GPT or Google Gemini — configurable via `Config.LLM_MODEL`.
- **Email**: `smtplib` over SMTP SSL (Gmail default).
- **Storage**: SQLAlchemy (SQLite for development, PostgreSQL for production) or Google Sheets via `gspread`.
- **Testing**: `pytest` + `pytest-flask` + `pytest-cov` + `unittest.mock`.
- **Configuration**: `.env` files + `python-dotenv` + `Config` class.
- **Version Control**: Git — `.env` and `credentials.json` MUST be in `.gitignore`.

## Development Workflow

1. **Identify** the next feature/function from the Specifications (SPEC-00 through SPEC-09).
2. **🔴 Red**: Write one or more failing tests in the corresponding `tests/test_*.py` file.
3. **Run `pytest`** — confirm all new tests fail.
4. **🟢 Green**: Write the minimum production code to make the failing tests pass.
5. **Run `pytest`** — confirm all tests pass.
6. **🔵 Refactor**: Improve code quality (readability, structure, naming) without changing behaviour. All tests MUST still pass.
7. **Check coverage**: Run `pytest --cov` — verify module meets its minimum threshold.
8. **Commit** with a descriptive message referencing the SPEC number (e.g., `feat(SPEC-03): implement Whisper transcription`).
9. **Repeat** for the next feature.

**Test naming convention**: `test_{method_name}_{scenario}_{expected_result}`

**Implementation phases**: Follow the order defined in the Implementation Plan — Phase 0 (Dashboard) through Phase 6 (Integration & Final Testing).

## Governance

- This constitution **supersedes** all ad-hoc development practices. All code contributions MUST comply with these principles.
- **Amendments** require: (1) documenting the proposed change, (2) updating this file with a version bump, and (3) propagating changes to affected templates and documentation.
- **Version bumps** follow semantic versioning: MAJOR for principle removals/redefinitions, MINOR for new principles or expansions, PATCH for clarifications.
- **Compliance review**: Before any module is considered complete, verify against the TDD Workflow Checklist (SPEC-10.9) and the Acceptance Criteria Checklist (Specifications Appendix A).
- Use `PRD.md`, `Specifications.md`, and `Implementation_Plan.md` as authoritative references for requirements and technical design.

**Version**: 1.0.0 | **Ratified**: 2026-03-15 | **Last Amended**: 2026-03-15
