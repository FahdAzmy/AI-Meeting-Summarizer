# Product Requirements Document (PRD)
## AI-Powered Meeting Assistant

| Field             | Details                                        |
|-------------------|------------------------------------------------|
| **Project Title** | AI-Powered Meeting Assistant                   |
| **Version**       | 1.0                                            |
| **Date**          | March 12, 2026                                 |
| **Status**        | Draft                                          |

---

## 1. Executive Summary

This project develops an **AI-powered meeting assistant** with a **web-based dashboard** that allows users to submit meeting links, trigger automated joining, and browse historical meeting records. The system automatically joins virtual meetings (Zoom, Google Meet, Microsoft Teams), records audio, transcribes conversations using Speech-to-Text APIs, generates intelligent summaries, and distributes reports to participants via email. Users can choose between **Google Sheets** or a **database (SQLite/PostgreSQL)** as their storage backend via the dashboard settings. All results are archived and accessible through the meetings history page.

The system addresses a critical communication gap: the lack of effective documentation and follow-up after online meetings, which leads to misunderstandings, forgotten tasks, and missed deadlines.

---

## 2. Problem Statement

In remote and hybrid work environments, meetings generate decisions, action items, and discussions that are often lost or poorly documented. Key pain points include:

- **Information loss** — Participants forget key details after meetings conclude.
- **No structured follow-up** — Decisions and task assignments are not formally tracked.
- **Manual effort** — Taking notes during meetings is distracting and error-prone.
- **Multi-disciplinary coordination** — Teams with diverse roles struggle to maintain alignment without clear records.

---

## 3. Product Vision & Goals

### Vision
To create a fully automated pipeline that transforms raw meeting audio into structured, actionable reports — eliminating the need for manual note-taking and follow-up.

### Primary Goals

| # | Goal                                     | Description                                                                                       |
|---|------------------------------------------|---------------------------------------------------------------------------------------------------|
| 1 | Web-Based Dashboard                     | Provide an intuitive UI for submitting meeting links, managing settings, and browsing history.     |
| 2 | Automatic Meeting Attendance & Recording | Join online meetings and record them in real time without manual intervention.                     |
| 3 | Speech-to-Text Conversion               | Accurately convert spoken language into written text using AI transcription models.                |
| 4 | Intelligent Summarisation                | Generate concise summaries capturing key points, decisions, and assigned tasks.                    |
| 5 | Participant Analysis                     | Assess engagement levels, contribution amounts, and interaction tone per participant.              |
| 6 | Flexible Storage Backend                | Allow users to choose between Google Sheets or a database for storing meeting data.                |
| 7 | Automated Email Reporting & Archiving    | Send meeting summaries to attendees and store results in the selected storage backend.             |

---

## 4. Target Users

| User Type            | Description                                                                   |
|----------------------|-------------------------------------------------------------------------------|
| **Project Managers** | Need clear records of decisions and task assignments from meetings.            |
| **Team Leads**       | Want to track participation and ensure accountability.                         |
| **Students/Academics** | Require structured meeting notes for group projects and thesis discussions.  |
| **Remote Workers**   | Need reliable documentation when attending meetings across time zones.         |

---

## 5. System Architecture Overview

The system follows a **sequential pipeline architecture** with six major modules, fronted by a web dashboard:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     0. FRONTEND DASHBOARD (Flask/FastAPI)                                    │
│   ┌─────────────────────┐   ┌──────────────────────┐   ┌──────────────────────────────────────────────────┐   │
│   │  Dashboard Page     │   │  Meetings History    │   │  Settings Page                                 │   │
│   │  • Meeting link     │   │  • Past meetings     │   │  • Storage backend toggle: DB / Google Sheets  │   │
│   │  • Participant emails│   │  • Summaries         │   │  • STT provider selection                      │   │
│   │  • [Join Meeting]   │   │  • Transcripts       │   │  • Email configuration                         │   │
│   └─────────┬───────────┘   └──────────────────────┘   └──────────────────────────────────────────────────┘   │
│             │ triggers pipeline                                                                              │
└─────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────┘
              ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌────────────────────┐    ┌──────────────────┐
│  1. Meeting  │───▶│  2. Audio        │───▶│  3. Transcription│───▶│ 4. Summarisation   │───▶│ 5. Output &      │
│  Access      │    │  Capture         │    │  (STT API)       │    │ & Analysis         │    │ Storage          │
│  (Selenium)  │    │  (OBS+WebSocket) │    │                  │    │                    │    │ (DB or Sheets)   │
└──────────────┘    └──────────────────┘    └──────────────────┘    └────────────────────┘    └──────────────────┘
```

### Module Descriptions

#### Module 0: Frontend Dashboard (Flask / FastAPI)
- **Dashboard Page** — Input form for meeting link and participant emails, with a "Join Meeting" button to trigger the pipeline.
- **Meetings History Page** — Displays a table/list of all past meetings with their summaries, transcripts, action items, and status. Users can search, filter, and open individual meeting reports.
- **Settings Page** — Allows users to toggle the storage backend between **Database** (SQLite/PostgreSQL) and **Google Sheets**. Based on this setting, all future meeting data is routed accordingly. Also includes STT provider selection and email configuration.
- Serves as the primary user interface; replaces command-line input.

#### Module 1: Meeting Access (Selenium)
- Opens the meeting link in an automated browser.
- Handles joining procedures (waiting room, microphone/camera permissions).
- Maintains continuous passive presence throughout the meeting.
- Provides the meeting window for OBS audio capture.

#### Module 2: Audio Capture (OBS + WebSocket)
- Starts and stops recording via Python WebSocket commands to OBS.
- Records raw audio from system sound output (bot does not speak).
- Saves the audio file to a predefined local location.

#### Module 3: Transcription (External STT API)
- Sends recorded audio to Whisper API, Deepgram, or AssemblyAI.
- Receives full transcription text and optional diarisation data.
- Normalises API output into a unified internal format.

#### Module 4: Summarisation & Analysis
- Generates structured summaries (key points, decisions, action items).
- Analyses speaker participation levels if diarisation is available.
- Uses LLM-based summarisation for high-quality, structured outputs.

#### Module 5: Output & Storage (Configurable Backend)
- Sends summary and key outputs to meeting participants via email.
- Stores transcription and summary in **the user's selected backend**: Google Sheets **or** Database (SQLite/PostgreSQL).
- The storage choice is configured via the dashboard Settings page.
- Maintains logs for meeting duration, STT results, and email delivery.

---

## 6. Functional Requirements

### 6.1 Frontend Dashboard Requirements

| ID    | Requirement                                                                                                          | Priority  |
|-------|----------------------------------------------------------------------------------------------------------------------|-----------|
| FR-D1 | The system shall provide a web-based dashboard accessible via a browser (Flask or FastAPI).                          | **Must**  |
| FR-D2 | The dashboard shall have a **Dashboard Page** with an input form for meeting link and participant emails.            | **Must**  |
| FR-D3 | The Dashboard Page shall include a "Join Meeting" button that triggers the full meeting processing pipeline.         | **Must**  |
| FR-D4 | The dashboard shall have a **Meetings History Page** that lists all previously processed meetings.                   | **Must**  |
| FR-D5 | The Meetings History Page shall display meeting date, platform, duration, summary, and processing status.            | **Must**  |
| FR-D6 | Users shall be able to click on any meeting in the history to view its full summary, transcript, and action items.   | **Must**  |
| FR-D7 | The dashboard shall have a **Settings Page** where users can toggle between Database and Google Sheets storage.      | **Must**  |
| FR-D8 | The Settings Page shall allow users to select the active STT provider (Whisper, Deepgram, or AssemblyAI).            | **Should**|
| FR-D9 | The Settings Page shall allow configuration of email sender credentials.                                             | **Should**|
| FR-D10| The dashboard shall show real-time status/progress of an active meeting session (joining, recording, processing).   | **Should**|
| FR-D11| The dashboard shall validate meeting links before submitting (check URL format and platform detection).              | **Should**|

### 6.2 Backend Pipeline Requirements

| ID   | Requirement                                                                                              | Priority  |
|------|----------------------------------------------------------------------------------------------------------|-----------|
| FR1  | The system shall allow the user to provide a meeting link (Zoom, Google Meet, or Microsoft Teams).       | **Must**  |
| FR2  | The system shall automatically open a browser and join the meeting as a passive participant via Selenium. | **Must**  |
| FR3  | The system shall initiate OBS through OBS WebSocket to record system audio during the meeting.           | **Must**  |
| FR4  | The system shall store the recorded audio locally in a supported audio format.                           | **Must**  |
| FR5  | The system shall send the recorded audio to an external STT API (Whisper, Deepgram, or AssemblyAI).     | **Must**  |
| FR6  | The system shall receive full meeting transcription text from the STT API.                               | **Must**  |
| FR7  | The system shall generate a structured meeting summary using an AI summarisation model.                  | **Must**  |
| FR8  | The system shall automatically send an email containing the summary to all meeting participants.         | **Must**  |
| FR9  | The system shall store data in the user-selected backend (Google Sheets **or** Database), as configured in the Settings Page. | **Must**  |
| FR10 | The system shall analyse speaker participation if diarisation metadata is provided by the STT API.       | **Should**|
| FR11 | The system shall provide logs for each session (join time, duration, transcription status, email status). | **Must**  |
| FR12 | The system shall handle errors (failed join, OBS issues, STT errors) through predefined fallback actions.| **Must**  |

---

## 7. Non-Functional Requirements

### 7.1 Performance
| ID   | Requirement                                                                                              |
|------|----------------------------------------------------------------------------------------------------------|
| NFR1 | Process and summarise a 30-minute meeting within 10 minutes after transcription.                         |
| NFR2 | STT response latency must remain within limits determined by API performance constraints.                |

### 7.2 Usability
| ID   | Requirement                                                                                              |
|------|----------------------------------------------------------------------------------------------------------|
| NFR3 | The web dashboard shall be responsive, visually clean, and intuitive for non-technical users.            |
| NFR4 | Logs should be readable and interpretable without technical expertise.                                   |
| NFR13| The Meetings History page shall load within 2 seconds even with 100+ meeting records.                   |
| NFR14| Switching storage backends via the Settings page shall take effect immediately for subsequent meetings.  |

### 7.3 Reliability
| ID   | Requirement                                                                                              |
|------|----------------------------------------------------------------------------------------------------------|
| NFR5 | The agent must remain connected to the meeting for the full duration without manual intervention.        |
| NFR6 | OBS must maintain continuous recording without interruption.                                             |

### 7.4 Security
| ID   | Requirement                                                                                              |
|------|----------------------------------------------------------------------------------------------------------|
| NFR7 | Participant emails must be handled securely and not exposed in logs.                                     |
| NFR8 | Transcriptions and summaries must be stored in secure storage (protected Sheets or database).            |

### 7.5 Scalability
| ID   | Requirement                                                                                              |
|------|----------------------------------------------------------------------------------------------------------|
| NFR9 | The system should support processing multiple meetings sequentially.                                     |
| NFR10| The architecture must support switching between STT providers with minimal configuration changes.        |

### 7.6 Maintainability
| ID    | Requirement                                                                                             |
|-------|---------------------------------------------------------------------------------------------------------|
| NFR11 | System components (Selenium, OBS, STT, email, storage) shall be modular and independently upgradable.  |
| NFR12 | Error logs should enable easy debugging for future updates.                                             |

---

## 8. Development Methodology — Test-Driven Development (TDD)

This project shall be developed using **Test-Driven Development (TDD)** as the primary development methodology. TDD ensures that every feature is validated by automated tests **before** the production code is written.

### 8.1 TDD Workflow (Red → Green → Refactor)

| Phase       | Activity                                                                                       |
|-------------|------------------------------------------------------------------------------------------------|
| **🔴 Red**     | Write a failing test that defines the expected behaviour of a feature or function.             |
| **🟢 Green**   | Write the **minimum** production code necessary to make the failing test pass.                |
| **🔵 Refactor**| Improve code quality (readability, structure, performance) without changing behaviour. All tests must still pass. |

### 8.2 TDD Rules

1. **No production code may be written without a failing test first.**
2. Each module (SPEC-00 through SPEC-09) must have its test file written **before** the module implementation.
3. Tests are the **living specification** — they serve as executable documentation of system behaviour.
4. All tests must pass before any code is merged or considered complete.
5. Test coverage target: **≥ 80%** line coverage for all modules.

### 8.3 Testing Levels

| Level             | Scope                                                                 | Tools                       |
|-------------------|-----------------------------------------------------------------------|-----------------------------|
| **Unit Tests**    | Individual functions and class methods in isolation.                  | `pytest`, `unittest.mock`   |
| **Integration Tests** | Module-to-module interactions (e.g., Transcription → Summarisation). | `pytest`, `pytest-flask`    |
| **System Tests**  | Full pipeline end-to-end with real/mock services.                    | `pytest`, manual validation |
| **Edge Case Tests** | Boundary conditions, invalid inputs, error paths.                  | `pytest`                    |

### 8.4 Benefits of TDD for This Project

- **Early bug detection** — Bugs in Selenium selectors, API response parsing, and email formatting are caught before integration.
- **Safe refactoring** — The test suite acts as a safety net when updating CSS selectors, switching STT providers, or modifying the pipeline.
- **Living documentation** — Tests document exactly how each module should behave, reducing ambiguity in the specification.
- **Confidence in external API integration** — Mock-based tests verify behaviour without incurring API costs during development.

---

## 9. Constraints

### 9.1 Technical Constraints
- **Selenium fragility** — UI changes in Zoom/Meet/Teams may break automation scripts.
- **OBS WebSocket dependency** — Configuration errors will interrupt recording.
- **External STT dependency** — Transcription accuracy is constrained by provider performance.
- **Internet requirement** — Stable connection needed for joining meetings and uploading audio.
- **Audio routing** — OS-level audio routing must be correctly configured for OBS to capture meeting audio.

### 9.2 Time & Budget Constraints
- STT APIs incur per-minute costs; testing must balance usage and budget.
- Development time is limited; the architecture avoids building ML models from scratch.

### 9.3 Platform Constraints
- **TDD discipline** — Requires strict adherence; writing tests before implementation adds upfront time but reduces debugging later.
- Meeting platforms restrict bot-like interactions; the bot is limited to passive attendance.
- Browser permissions and OS limitations may affect automated audio capture.

---

## 10. Use Cases

### Actors
| Actor              | Role                                                          |
|--------------------|---------------------------------------------------------------|
| User               | Interacts via the web dashboard to manage meetings.           |
| Meeting Platform   | Hosts the meeting (Zoom/Teams/Google Meet).                   |
| STT API Provider   | Processes audio and returns transcription.                    |
| Email Service      | Delivers meeting summaries to participants.                   |
| Storage Service    | Persists transcription and summary data (Google Sheets / DB). |

### Use Case Summary

| #  | Use Case                     | Input                                            | Output                                      |
|----|------------------------------|--------------------------------------------------|----------------------------------------------|
| UC1| Submit Meeting via Dashboard | Meeting link + emails entered in Dashboard Page  | Pipeline triggered; status shown live        |
| UC2| Start Meeting Automation     | Meeting link (from dashboard)                    | Agent joins meeting                          |
| UC3| Record Audio                 | Meeting audio stream                             | Saved audio file                             |
| UC4| Transcribe Audio             | Audio file                                       | Full transcription text                      |
| UC5| Generate Summary             | Transcription text                               | Structured summary with action items         |
| UC6| Distribute & Store Summary   | Summary, email list, storage choice              | Emails sent; data stored per selected backend|
| UC7| Browse Meeting History       | User navigates to Meetings History page          | List of past meetings with summaries         |
| UC8| View Meeting Details         | User clicks on a meeting record                  | Full summary, transcript, and action items   |
| UC9| Configure Storage Backend    | User toggles DB/Sheets in Settings page          | Subsequent meetings use selected backend     |

---

## 11. Technology Stack

| Component            | Technology                                          |
|----------------------|-----------------------------------------------------|
| Programming Language | Python 3.10+                                        |
| **Frontend/Dashboard** | **Flask or FastAPI + Jinja2 Templates (HTML/CSS/JS)** |
| Meeting Joining      | Selenium WebDriver + Chrome/Edge                    |
| Audio Recording      | OBS Studio + OBS WebSocket (obs-websocket-py)       |
| Speech-to-Text       | Whisper API (primary) / Deepgram / AssemblyAI       |
| Summarisation        | OpenAI GPT / Google Gemini / open-source LLM        |
| Email Delivery       | SMTP (smtplib) or Gmail API                         |
| Data Storage         | Google Sheets API (gspread) **or** SQLite/PostgreSQL (user-selectable via dashboard) |
| ORM (for DB mode)    | SQLAlchemy (when database storage is selected)      |
| Configuration        | `.env` files + Python `dotenv`                      |
| Logging              | Python `logging` module                             |

---

## 12. Evaluation Metrics

| Metric                | Definition                                                      | Target          |
|-----------------------|-----------------------------------------------------------------|-----------------|
| Audio Quality Score   | RMS variation, noise levels in recorded audio.                  | Acceptable SNR  |
| STT Accuracy          | Word Error Rate (WER) of transcription.                         | < 15% WER       |
| End-to-End Latency    | Time from meeting end to summary readiness.                     | < 10 min        |
| Email Success Rate    | Percentage of summary emails delivered successfully.            | > 95%           |
| Storage Write Success | Percentage of successful write operations to Sheets/DB.         | 100%            |

---

## 13. Risks & Mitigations

| Risk                                        | Impact   | Mitigation                                                      |
|---------------------------------------------|----------|-----------------------------------------------------------------|
| Meeting platform UI changes break Selenium  | High     | Modular selectors; version-pinned browser; fallback strategies. |
| OBS WebSocket connection failure            | High     | Health checks; auto-reconnect logic; pre-flight validation.     |
| Poor transcription accuracy (noisy audio)   | Medium   | Audio preprocessing; allow STT provider switching.              |
| STT API downtime                            | Medium   | Support multiple providers; retry logic with backoff.           |
| Email blocked by spam filter                | Low      | Use authenticated SMTP; proper email headers.                   |
| Privacy/security breach of recordings       | High     | Encrypt files at rest; secure credentials; auto-cleanup.        |

---

## 14. Success Criteria

The project is considered successful when:

1. ✅ The web dashboard is accessible and users can submit meeting links and emails via the UI.
2. ✅ The agent can join a meeting via link and remain connected for the full duration.
3. ✅ Audio is recorded without interruption and saved in a valid format.
4. ✅ Transcription is generated with acceptable accuracy (< 15% WER).
5. ✅ A structured summary with key points, decisions, and action items is produced.
6. ✅ Summary emails are delivered to all listed participants.
7. ✅ Users can toggle between Google Sheets and Database storage via the Settings page.
8. ✅ All data is stored in the selected backend and accessible on the Meetings History page.
9. ✅ The end-to-end pipeline completes within 10 minutes after meeting end.
10. ✅ All modules have corresponding test files written **before** implementation (TDD).
11. ✅ Automated test suite achieves ≥ 80% code coverage across all modules.
12. ✅ All tests pass before each module is considered complete.
