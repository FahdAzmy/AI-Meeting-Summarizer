# project Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-26

## Active Technologies
- Python 3.10+ + `selenium>=4.15.0`, `webdriver-manager>=4.0.0` (003-meeting-access)
- Config-driven CSS selector dictionaries (JSON), Database status writes for the overarching pipeline. (003-meeting-access)
- Python 3.10+ + `obsws-python>=1.3.1` (004-audio-capture)
- Local file system (outputting `.wav` files). (004-audio-capture)
- Python 3.10+ + `requests`, `openai>=1.0`, `deepgram-sdk`, `assemblyai` (005-transcription)
- N/A (Module receives a file path and returns dict memory structures) (005-transcription)
- Python 3.10+ + `openai>=1.0` (for LLM), `pydantic>=2.0` (for strict JSON schema outputs from LLM calls) (006-summarisation)
- N/A (Module receives a dict and returns a dict in memory) (006-summarisation)
- Python 3.10+ + `motor` (async MongoDB driver), `beanie` (async ODM), `aiosmtplib` (async SMTP), `gspread` (Google Sheets SDK), `pandas` (for CSV fallbacks). (007-output-storage)
- MongoDB (local or Atlas) and local filesystem (for `.csv` fallbacks). (007-output-storage)
- Python 3.10+ + `fastapi` (BackgroundTasks), `asyncio`, `beanie` (for real-time tracking) (008-pipeline-orchestrator)
- MongoDB (Updating live Document instances) (008-pipeline-orchestrator)
- [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION] (009-configuration-environment)
- [if applicable, e.g., PostgreSQL, CoreData, files or N/A] (009-configuration-environment)
- Python 3.11+ + Pydantic, pydantic-settings, dotenv (009-configuration-environment)
- Environment variables, `.env` file, MongoDB (via Beanie ODM, for dashboard overrides) (009-configuration-environment)
- Python 3.11 (backend), TypeScript/Next.js 15 (frontend) + FastAPI, openpyxl (Excel), reportlab (PDF), Beanie ODM (MongoDB) (010-meeting-export)
- MongoDB (existing `meetings` collection, read-only for this feature) (010-meeting-export)

- TypeScript, React 18, Node.js 18+ + Next.js 14+ (App Router), Tailwind CSS, React Hook Form (for forms) (002-frontend-dashboard)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

npm test; npm run lint

## Code Style

TypeScript, React 18, Node.js 18+: Follow standard conventions

## Recent Changes
- 010-meeting-export: Added Python 3.11 (backend), TypeScript/Next.js 15 (frontend) + FastAPI, openpyxl (Excel), reportlab (PDF), Beanie ODM (MongoDB)
- 009-configuration-environment: Added Python 3.11+ + Pydantic, pydantic-settings, dotenv
- 009-configuration-environment: Added [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
