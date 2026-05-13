<p align="center">
  <h1 align="center">🤖 AI Meeting Summarizer</h1>
  <p align="center">
    An end-to-end system that autonomously joins virtual meetings, records audio, transcribes speech, generates AI-powered summaries, and delivers structured reports.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/MongoDB-6+-47A248?logo=mongodb&logoColor=white" alt="MongoDB" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Pipeline Stages](#-pipeline-stages)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Environment Variables](#-environment-variables)
- [Running the Application](#-running-the-application)
- [API Reference](#-api-reference)
- [Modules Deep Dive](#-modules-deep-dive)
- [Export Formats](#-export-formats)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**AI Meeting Summarizer** is a graduation project that automates the entire lifecycle of virtual meeting documentation. Instead of manually taking notes, simply provide a meeting link — the system will:

1. **Join** the meeting autonomously via Selenium WebDriver
2. **Record** system audio using OBS Studio's WebSocket API
3. **Transcribe** the audio using enterprise-grade STT providers (Deepgram, AssemblyAI, or OpenAI Whisper)
4. **Summarize** the transcript with an LLM (GPT-4o, Claude, LLaMA, Mistral, or any OpenAI-compatible API)
5. **Deliver** the structured report via email and persist it to MongoDB

### Supported Platforms

| Platform | Join Method | Status |
|----------|-------------|--------|
| Google Meet | Selenium WebDriver | ✅ Supported |
| Microsoft Teams | Selenium WebDriver | ✅ Supported |
| Zoom | Selenium WebDriver / Zoom Meeting SDK | ✅ Supported |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 16)                     │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌────────┐  │
│  │Dashboard │  │Meeting History│  │  Detail  │  │Settings│  │
│  │  + Form  │  │    List      │  │   View   │  │  Page  │  │
│  └────┬─────┘  └──────┬───────┘  └────┬─────┘  └────┬───┘  │
│       │               │               │              │      │
└───────┼───────────────┼───────────────┼──────────────┼──────┘
        │  REST API     │   GET         │   GET        │
        ▼               ▼               ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Orchestrator (Pipeline)                 │    │
│  │                                                     │    │
│  │  JOINING → RECORDING → TRANSCRIBING → SUMMARISING   │    │
│  │                                    → DELIVERING      │    │
│  └──┬──────────┬───────────┬───────────┬───────────┬───┘    │
│     │          │           │           │           │        │
│  ┌──▼───┐  ┌──▼────┐  ┌───▼───┐  ┌────▼────┐  ┌──▼────┐   │
│  │ MA   │  │  AC   │  │  TR   │  │   SM    │  │  OS   │   │
│  │      │  │       │  │       │  │         │  │       │   │
│  │Seleni│  │ OBS   │  │Deepgr.│  │ GPT-4o  │  │MongoDB│   │
│  │um Bot│  │WebSoc.│  │Assemb.│  │ Claude  │  │ Email │   │
│  │      │  │       │  │Whisper│  │ LLaMA   │  │       │   │
│  └──────┘  └───────┘  └───────┘  └─────────┘  └───────┘   │
└─────────────────────────────────────────────────────────────┘
        MA = Meeting Access    AC = Audio Capture
        TR = Transcription     SM = Summarisation
        OS = Output Storage
```

---

## 🛠 Tech Stack

### Backend
| Category | Technology |
|----------|-----------|
| Framework | FastAPI 0.110+ with Uvicorn |
| Language | Python 3.11+ |
| Database | MongoDB with Beanie ODM |
| Browser Automation | Selenium WebDriver + ChromeDriver |
| Audio Recording | OBS Studio via obsws-python WebSocket |
| Speech-to-Text | Deepgram, AssemblyAI, OpenAI Whisper |
| LLM / Summarization | Any OpenAI-compatible API (GPT-4o, Groq, Ollama, etc.) |
| Email Delivery | aiosmtplib (async SMTP) |
| Export | openpyxl (Excel), ReportLab (PDF) |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Config | Pydantic Settings + python-dotenv |

### Frontend
| Category | Technology |
|----------|-----------|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript 5 |
| UI Library | React 19 |
| Styling | Tailwind CSS 4 |
| Testing | Jest, React Testing Library, Playwright |
| Zoom Integration | @zoom/meetingsdk |

---

## ⚙️ Pipeline Stages

The orchestrator (`src/orchestrator.py`) manages a 6-stage asynchronous pipeline:

| # | Stage | Status | Module | Description |
|---|-------|--------|--------|-------------|
| 1 | **Join Meeting** | `JOINING` | `MeetingAccess` | Selenium bot detects platform, navigates to meeting URL, handles pre-join UI (camera/mic off, bot name), and clicks "Join" |
| 2 | **Record Audio** | `RECORDING` | `AudioCapture` | Connects to OBS via WebSocket, starts recording system audio, waits for meeting to end or all participants to leave |
| 3 | **Transcribe** | `TRANSCRIBING` | `Transcription` | Extracts audio from video (ffmpeg MP4→WAV), sends to configured STT provider with automatic fallback chain |
| 4 | **Summarize** | `SUMMARISING` | `Summarisation` | Sends transcript to LLM with structured prompts, extracts summary, action items, decisions, and follow-ups |
| 5 | **Deliver** | `DELIVERING` | `OutputStorage` | Persists meeting document to MongoDB, renders HTML email report, sends via SMTP to recipients |
| 6 | **Done** | `COMPLETED` | — | Terminal success state; frontend redirects to history |

All blocking I/O (Selenium, OBS) is offloaded to a thread pool via `asyncio.to_thread()` to keep FastAPI's event loop responsive.

---

## 📁 Project Structure

```
project/
├── backend/
│   ├── config/
│   │   ├── settings.py          # Pydantic Settings (all env vars)
│   │   └── selectors.json       # Platform-specific CSS/XPath selectors
│   ├── modules/                 # 🧠 Core AI Pipeline Modules
│   │   ├── meeting_access.py    # Selenium bot facade
│   │   ├── _meeting_access/     # Internal: browser, detection, strategies/
│   │   │   ├── strategies/
│   │   │   │   ├── google_meet.py
│   │   │   │   ├── teams.py
│   │   │   │   ├── zoom.py
│   │   │   │   └── zoom_sdk.py
│   │   │   ├── browser.py       # Chrome options builder
│   │   │   ├── detection.py     # Platform URL detection
│   │   │   └── monitor.py       # Meeting end/alone detection
│   │   ├── audio_capture.py     # OBS WebSocket bridge
│   │   ├── transcription.py     # STT facade
│   │   ├── _transcription/      # Internal: providers, normalisers, service
│   │   ├── summarisation.py     # LLM facade
│   │   ├── _summarisation/      # Internal: prompts, schemas, analytics
│   │   ├── output_storage.py    # Storage/email facade
│   │   ├── _output_storage/     # Internal: database, email, renderer
│   │   ├── errors.py            # Meeting Access error hierarchy
│   │   ├── stt_errors.py        # Transcription error hierarchy
│   │   ├── llm_errors.py        # Summarisation error hierarchy
│   │   └── storage_errors.py    # Output Storage error hierarchy
│   ├── src/
│   │   ├── main.py              # FastAPI app entrypoint
│   │   ├── orchestrator.py      # Central pipeline orchestrator
│   │   ├── models/
│   │   │   └── meeting.py       # Beanie ODM Meeting document
│   │   ├── routes/
│   │   │   ├── api.py           # /trigger, /join, /status, /meetings
│   │   │   ├── export.py        # /export (Excel & PDF downloads)
│   │   │   └── zoom.py          # Zoom SDK JWT signature endpoint
│   │   └── helpers/
│   │       ├── config.py        # FastAPI-specific settings
│   │       ├── db.py            # MongoDB connection (Motor + Beanie)
│   │       ├── security.py      # JWT auth, password hashing
│   │       ├── logging_config.py# Structured logging
│   │       ├── excel_generator.py
│   │       ├── pdf_generator.py
│   │       └── zoom_sdk.py      # Zoom URL parser & JWT generator
│   ├── tests/                   # Unit & integration tests
│   ├── .env.example             # Environment variable template
│   └── requirements.txt         # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # Dashboard (meeting form + status)
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── history/         # Meeting history page
│   │   │   ├── settings/        # Settings page
│   │   │   └── zoom-meeting/    # Zoom SDK integration page
│   │   ├── components/
│   │   │   ├── dashboard/       # MeetingForm, StatusPanel
│   │   │   ├── history/         # Meeting history list
│   │   │   ├── detail/          # Meeting detail view
│   │   │   ├── settings/        # Settings components
│   │   │   └── ui/              # Reusable UI (Toast, etc.)
│   │   └── lib/                 # API client, utilities
│   ├── package.json
│   └── tsconfig.json
│
├── .gitignore
└── README.md
```

---

## 📦 Prerequisites

Before running the application, ensure the following are installed:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 18+ | Frontend runtime |
| **MongoDB** | 6+ | Meeting data persistence |
| **OBS Studio** | 30+ | Audio recording (must have WebSocket server enabled) |
| **Google Chrome** | Latest | Selenium browser automation |
| **ffmpeg** | Latest | Audio extraction from video (MP4 → WAV) |

### OBS Studio Setup

1. Install [OBS Studio](https://obsproject.com/)
2. Go to **Tools → WebSocket Server Settings**
3. Enable the WebSocket server on port `4455`
4. Set an authentication password (match it in your `.env`)
5. Configure an audio-only recording profile pointing to your `RECORDINGS_DIR`

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/FahdAzmy/AI-Meeting-Summarizer.git
cd AI-Meeting-Summarizer
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Configure Environment Variables

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys and credentials

# Frontend
# Ensure frontend/.env has: NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 5. Start MongoDB

```bash
# If using local MongoDB
mongod --dbpath /path/to/your/data
```

---

## 🔐 Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

### STT (Speech-to-Text) Providers

```env
STT_PROVIDER=deepgram          # Options: deepgram, assemblyai, whisper
DEEPGRAM_API_KEY=your_key
ASSEMBLYAI_API_KEY=your_key
WHISPER_API_KEY=your_key       # OpenAI API key
```

### LLM (Summarization) — Provider Agnostic

Switch providers by changing just three values:

```env
# OpenAI (default)
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-...

# Groq (ultra-fast, free tier)
# LLM_BASE_URL=https://api.groq.com/openai/v1
# LLM_MODEL=llama3-70b-8192

# Ollama (local, no API key needed)
# LLM_BASE_URL=http://localhost:11434/v1
# LLM_MODEL=llama3
# LLM_API_KEY=no-key

# OpenRouter (100+ models)
# LLM_BASE_URL=https://openrouter.ai/api/v1
# LLM_MODEL=anthropic/claude-3-haiku
```

### OBS WebSocket

```env
OBS_HOST=localhost
OBS_PORT=4455
OBS_PASSWORD=your_obs_password
```

### MongoDB & Email

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=ai_summarizer

EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
```

### Zoom Meeting SDK (Optional)

```env
ZOOM_SDK_CLIENT_ID=your_client_id
ZOOM_SDK_CLIENT_SECRET=your_client_secret
```

---

## ▶️ Running the Application

### Start the Backend

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

### Start the Frontend

```bash
cd frontend
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

### Launch OBS Studio

Open OBS Studio with WebSocket server enabled before triggering any meeting pipeline.

---

## 📡 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/trigger` | Launch the full AI pipeline (returns `session_id`) |
| `GET` | `/api/status/{session_id}` | Poll pipeline progress |
| `GET` | `/api/meetings` | List all meeting records |
| `GET` | `/api/meetings/{id}` | Get meeting detail with full report |
| `GET` | `/api/settings` | Get current system settings |
| `POST` | `/api/settings` | Update system settings |

### Export Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/export/meetings/excel` | Download all meetings as Excel |
| `GET` | `/api/export/meetings/{id}/excel` | Download single meeting as Excel |
| `GET` | `/api/export/meetings/{id}/pdf` | Download single meeting as PDF |

### Zoom SDK Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/zoom/signature` | Generate JWT signature for Zoom SDK |

### Trigger Pipeline Example

```bash
curl -X POST http://localhost:8000/api/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_link": "https://meet.google.com/abc-defg-hij",
    "emails": ["team@example.com"],
    "storage": "email"
  }'
```

**Response (202 Accepted):**
```json
{
  "session_id": "session_a1b2c3d4",
  "message": "Pipeline launched successfully. Track progress via the dashboard.",
  "meeting_link": "https://meet.google.com/abc-defg-hij",
  "storage": "email"
}
```

---

## 🧠 Modules Deep Dive

### 1. Meeting Access (`modules/meeting_access.py`)

Autonomous Selenium bot with platform-specific join strategies:

- **Platform Detection** — URL pattern matching for Google Meet, Teams, Zoom
- **Strategy Pattern** — Dedicated strategy classes for each platform's pre-join UI
- **Teams URL Rewriting** — Converts native app URLs to web client URLs
- **Lobby Handling** — Waits for host admission with configurable timeout
- **End Detection** — Monitors participant count and end-of-meeting screens
- **Grace Period** — 30-second buffer before concluding "alone in meeting"

### 2. Audio Capture (`modules/audio_capture.py`)

OBS Studio WebSocket bridge:

- **Health Check** — Verifies OBS connectivity before recording
- **Start/Stop** — Programmatic recording lifecycle
- **Path Resolution** — Handles multiple OBS response formats
- **Custom Error Hierarchy** — `OBSConnectionError`, `RecordingStartError`, `EmptyRecordingError`

### 3. Transcription (`modules/transcription.py`)

Multi-provider STT engine with automatic fallback:

- **Providers** — Deepgram (diarized), AssemblyAI (async polling), OpenAI Whisper
- **Fallback Chain** — Automatic retry with next provider on failure
- **Normalisation** — Unified `TranscriptResult` format across all providers
- **Speaker Diarisation** — Per-speaker timestamps when provider supports it
- **Audio Validation** — Size checks (25 MB Whisper / 500 MB Deepgram limit)

### 4. Summarisation (`modules/summarisation.py`)

Provider-agnostic LLM integration:

- **Structured Output** — JSON schema for summary, action items, decisions, follow-ups
- **Speaker Detection** — LLM-inferred speaker identification when STT diarisation unavailable
- **Participation Analytics** — Speaking time, turn count, most active speaker
- **Prompt Engineering** — Optimized system prompts for meeting content extraction

### 5. Output Storage (`modules/output_storage.py`)

Multi-backend delivery system:

- **MongoDB Persistence** — Full meeting document with Beanie ODM
- **Email Reports** — HTML-rendered email with Jinja2-style templates
- **SMTP Delivery** — Async email dispatch via aiosmtplib

---

## 📊 Export Formats

The system supports exporting meeting reports in multiple formats:

| Format | Scope | Details |
|--------|-------|---------|
| **Excel (.xlsx)** | Single or All meetings | Summary, action items, decisions in tabular format |
| **PDF** | Single meeting | Formatted report with sections and styling |

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_orchestrator.py
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm test

# E2E tests (Playwright)
npx playwright test
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## 📄 License

This project was developed as a graduation project. Please contact the authors for licensing information.

---

<p align="center">
  Built with ❤️ as a Graduation Project
</p>
