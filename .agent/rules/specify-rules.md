# project Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-15

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
- 008-pipeline-orchestrator: Added Python 3.10+ + `fastapi` (BackgroundTasks), `asyncio`, `beanie` (for real-time tracking)
- 007-output-storage: Added Python 3.10+ + `motor` (async MongoDB driver), `beanie` (async ODM), `aiosmtplib` (async SMTP), `gspread` (Google Sheets SDK), `pandas` (for CSV fallbacks).
- 006-summarisation: Added Python 3.10+ + `openai>=1.0` (for LLM), `pydantic>=2.0` (for strict JSON schema outputs from LLM calls)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
