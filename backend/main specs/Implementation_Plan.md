# Implementation Plan
## AI-Powered Meeting Assistant

| Field             | Details                                        |
|-------------------|------------------------------------------------|
| **Project Title** | AI-Powered Meeting Assistant                   |
| **Version**       | 1.0                                            |
| **Date**          | March 12, 2026                                 |
| **Status**        | Draft                                          |

---

## 1. Overview

This document outlines the complete implementation plan for the AI-Powered Meeting Assistant — a Python-based system with a **web dashboard** that allows users to submit meeting links, configure storage preferences (Database or Google Sheets), and browse meeting history. The backend pipeline automatically joins virtual meetings, records audio, generates transcriptions and intelligent summaries, and delivers results to participants.

---

## 2. Project Structure

```
ai-meeting-assistant/
├── app.py                         # Flask/FastAPI web server (dashboard entry point)
├── main.py                        # Pipeline orchestrator (called from web routes)
├── config.py                      # Centralised configuration management
├── models.py                      # SQLAlchemy database models
├── .env                           # Environment variables (API keys, credentials)
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
│
├── frontend/
│   ├── templates/                 # Jinja2 HTML templates
│   │   ├── base.html              # Base layout (navbar, footer)
│   │   ├── dashboard.html         # Dashboard Page (meeting link input + join button)
│   │   ├── history.html           # Meetings History Page (list of past meetings)
│   │   ├── meeting_detail.html    # Meeting Detail Page (full summary/transcript view)
│   │   └── settings.html          # Settings Page (storage toggle, STT, email config)
│   └── static/
│       ├── css/
│       │   └── style.css          # Dashboard styles
│       ├── js/
│       │   └── app.js             # Frontend interactivity (form validation, live status)
│       └── img/                   # Static images/icons
│
├── modules/
│   ├── __init__.py
│   ├── meeting_access.py          # Module 1: Selenium-based meeting joiner
│   ├── audio_capture.py           # Module 2: OBS WebSocket audio recorder
│   ├── transcription.py           # Module 3: STT API integration
│   ├── summarisation.py           # Module 4: LLM-based summarisation & analysis
│   └── output_storage.py          # Module 5: Email delivery & data storage
│
├── utils/
│   ├── __init__.py
│   ├── logger.py                  # Logging utility
│   ├── email_helper.py            # Email sending helpers
│   ├── sheets_helper.py           # Google Sheets API helpers
│   └── db_helper.py               # Database (SQLAlchemy) helpers
│
├── recordings/                    # Saved audio files (auto-created)
├── transcripts/                   # Saved transcription files (auto-created)
├── summaries/                     # Saved summary files (auto-created)
├── logs/                          # Application logs (auto-created)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Shared fixtures (test client, test DB, mocks)
│   ├── test_dashboard.py          # TDD tests for SPEC-00 (routes)
│   ├── test_models.py             # TDD tests for SPEC-08 (database models)
│   ├── test_meeting_access.py     # TDD tests for SPEC-01
│   ├── test_audio_capture.py      # TDD tests for SPEC-02
│   ├── test_transcription.py      # TDD tests for SPEC-03
│   ├── test_summarisation.py      # TDD tests for SPEC-04
│   ├── test_output_storage.py     # TDD tests for SPEC-05
│   ├── test_pipeline.py           # TDD tests for SPEC-06
│   ├── test_config.py             # TDD tests for SPEC-07
│   └── test_logger.py             # TDD tests for SPEC-09
```

---

## 3. Technology Stack & Dependencies

### 3.1 Core Dependencies

```
# requirements.txt
flask>=3.0.0                       # or: fastapi>=0.110.0 + uvicorn>=0.27.0
flask-sqlalchemy>=3.1.0
sqlalchemy>=2.0.0
selenium>=4.15.0
webdriver-manager>=4.0.0
obs-websocket-py>=1.0.0
openai>=1.0.0
google-generativeai>=0.3.0
assemblyai>=0.20.0
deepgram-sdk>=3.0.0
gspread>=5.12.0
oauth2client>=4.1.3
python-dotenv>=1.0.0
pydub>=0.25.1

# === TDD / Testing ===
pytest>=8.0.0
pytest-flask>=1.3.0
pytest-cov>=5.0.0
unittest-mock                      # (built-in, listed for documentation)
```

### 3.2 External Services

| Service           | Purpose                         | Authentication               |
|-------------------|---------------------------------|------------------------------|
| OpenAI Whisper API | Primary STT provider           | API Key                      |
| Deepgram          | Alternative STT provider        | API Key                      |
| AssemblyAI        | Alternative STT provider        | API Key                      |
| OpenAI GPT / Gemini | LLM summarisation             | API Key                      |
| Gmail SMTP        | Email delivery                  | App Password                 |
| Google Sheets API | Data storage                    | OAuth2 Service Account       |
| OBS Studio        | Audio recording                 | OBS WebSocket (local)        |

### 3.3 System Prerequisites

- Python 3.10+
- OBS Studio (installed with WebSocket plugin enabled)
- Google Chrome or Microsoft Edge browser
- ChromeDriver / EdgeDriver (auto-managed by `webdriver-manager`)
- Stable internet connection

---

## 4. Module Implementation Details

---

### 4.0 Module 0: Frontend Dashboard (`app.py` + `frontend/`)

**Purpose:** Provide a web-based user interface for managing meetings, configuring settings, and browsing history.

#### Technology Choice

| Option   | Pros                                    | Cons                              | Recommendation |
|----------|-----------------------------------------|-----------------------------------|----------------|
| Flask    | Simple, Jinja2 built-in, large ecosystem | Synchronous by default            | ✅ **Chosen**  |
| FastAPI  | Async, auto-docs, modern                 | Slightly more setup for templates | Alternative    |

#### Pages & Routes

| Route                    | Method     | Page / Action                                              |
|--------------------------|------------|------------------------------------------------------------|
| `/`                      | GET        | **Dashboard Page** — meeting link input form + join button |
| `/join`                  | POST       | Trigger the meeting pipeline (accepts link + emails)       |
| `/status/<session_id>`   | GET        | Real-time pipeline status (JSON or SSE)                    |
| `/history`               | GET        | **Meetings History Page** — list of all past meetings      |
| `/history/<meeting_id>`  | GET        | **Meeting Detail Page** — full summary & transcript        |
| `/settings`              | GET        | **Settings Page** — storage toggle, STT, email config      |
| `/settings`              | POST       | Save updated settings                                      |

#### Dashboard Page (`frontend/templates/dashboard.html`)

```html
<!-- Key UI elements -->
<form action="/join" method="POST" id="meeting-form">
    <div class="form-group">
        <label>Meeting Link</label>
        <input type="url" name="meeting_link" placeholder="https://meet.google.com/..." required>
        <span class="platform-badge" id="platform-detect"><!-- auto-detected --></span>
    </div>
    <div class="form-group">
        <label>Participant Emails</label>
        <textarea name="emails" placeholder="alice@example.com, bob@example.com" required></textarea>
    </div>
    <button type="submit" class="btn-join">🚀 Join Meeting</button>
</form>
<div id="live-status" class="status-panel" style="display:none;">
    <!-- Real-time pipeline progress -->
</div>
```

#### Meetings History Page (`frontend/templates/history.html`)

```html
<!-- Displays a table of all past meetings -->
<table class="meetings-table">
    <thead>
        <tr>
            <th>Date</th>
            <th>Platform</th>
            <th>Duration</th>
            <th>Summary Preview</th>
            <th>Status</th>
            <th>Action</th>
        </tr>
    </thead>
    <tbody>
        {% for meeting in meetings %}
        <tr>
            <td>{{ meeting.date }}</td>
            <td><span class="badge badge-{{ meeting.platform }}">{{ meeting.platform }}</span></td>
            <td>{{ meeting.duration }} min</td>
            <td>{{ meeting.summary[:100] }}...</td>
            <td><span class="status-{{ meeting.status }}">{{ meeting.status }}</span></td>
            <td><a href="/history/{{ meeting.id }}" class="btn-view">View Details</a></td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

#### Settings Page (`frontend/templates/settings.html`)

```html
<form action="/settings" method="POST">
    <!-- Storage Backend Toggle -->
    <div class="setting-group">
        <h3>📦 Storage Backend</h3>
        <div class="toggle-group">
            <label>
                <input type="radio" name="storage_backend" value="database"
                       {{ 'checked' if settings.storage_backend == 'database' }}>
                🗄️ Database (SQLite / PostgreSQL)
            </label>
            <label>
                <input type="radio" name="storage_backend" value="google_sheets"
                       {{ 'checked' if settings.storage_backend == 'google_sheets' }}>
                📊 Google Sheets
            </label>
        </div>
    </div>

    <!-- STT Provider Selection -->
    <div class="setting-group">
        <h3>🎤 STT Provider</h3>
        <select name="stt_provider">
            <option value="whisper" {{ 'selected' if settings.stt_provider == 'whisper' }}>Whisper API</option>
            <option value="deepgram" {{ 'selected' if settings.stt_provider == 'deepgram' }}>Deepgram</option>
            <option value="assemblyai" {{ 'selected' if settings.stt_provider == 'assemblyai' }}>AssemblyAI</option>
        </select>
    </div>

    <!-- Email Configuration -->
    <div class="setting-group">
        <h3>📧 Email Settings</h3>
        <input type="email" name="email_sender" value="{{ settings.email_sender }}" placeholder="Sender email">
        <input type="password" name="email_password" placeholder="App password">
    </div>

    <button type="submit" class="btn-save">💾 Save Settings</button>
</form>
```

#### Flask App (`app.py`)

```python
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Meeting, Settings
import threading

app = Flask(__name__, template_folder="frontend/templates",
            static_folder="frontend/static")
app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URI
app.config["SECRET_KEY"] = Config.SECRET_KEY
db.init_app(app)

@app.route("/")
def dashboard():
    """Dashboard Page — meeting link input + join button."""
    return render_template("dashboard.html")

@app.route("/join", methods=["POST"])
def join_meeting():
    """Trigger the meeting pipeline in a background thread."""
    meeting_link = request.form["meeting_link"]
    emails = [e.strip() for e in request.form["emails"].split(",")]
    
    # Get current storage preference
    settings = Settings.query.first()
    storage_backend = settings.storage_backend if settings else "database"
    
    # Run pipeline in background thread
    from main import run_pipeline
    thread = threading.Thread(
        target=run_pipeline,
        args=(meeting_link, emails, storage_backend)
    )
    thread.start()
    
    return redirect(url_for("dashboard"))

@app.route("/history")
def history():
    """Meetings History Page — list all past meetings."""
    meetings = Meeting.query.order_by(Meeting.date.desc()).all()
    return render_template("history.html", meetings=meetings)

@app.route("/history/<int:meeting_id>")
def meeting_detail(meeting_id):
    """Meeting Detail Page — full summary and transcript."""
    meeting = Meeting.query.get_or_404(meeting_id)
    return render_template("meeting_detail.html", meeting=meeting)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Settings Page — storage toggle, STT provider, email config."""
    settings_obj = Settings.query.first()
    if request.method == "POST":
        if not settings_obj:
            settings_obj = Settings()
            db.session.add(settings_obj)
        settings_obj.storage_backend = request.form["storage_backend"]
        settings_obj.stt_provider = request.form["stt_provider"]
        settings_obj.email_sender = request.form.get("email_sender", "")
        settings_obj.email_password = request.form.get("email_password", "")
        db.session.commit()
        return redirect(url_for("settings"))
    return render_template("settings.html", settings=settings_obj)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
```

#### Database Models (`models.py`)

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Meeting(db.Model):
    """Stores each processed meeting's data."""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), unique=True, nullable=False)
    meeting_link = db.Column(db.String(500), nullable=False)
    platform = db.Column(db.String(50))          # google_meet | zoom | teams
    date = db.Column(db.DateTime, default=datetime.utcnow)
    duration_minutes = db.Column(db.Integer)
    participants = db.Column(db.Text)             # comma-separated emails
    transcript = db.Column(db.Text)               # full transcription
    summary = db.Column(db.Text)                  # generated summary
    action_items = db.Column(db.Text)             # JSON string of action items
    decisions = db.Column(db.Text)                # JSON string of decisions
    speaker_stats = db.Column(db.Text)            # JSON string of participation
    status = db.Column(db.String(20), default="pending")  # pending|recording|processing|completed|failed
    audio_file_path = db.Column(db.String(500))
    storage_backend = db.Column(db.String(20))    # database | google_sheets

class Settings(db.Model):
    """Stores user preferences (singleton row)."""
    id = db.Column(db.Integer, primary_key=True)
    storage_backend = db.Column(db.String(20), default="database")  # database | google_sheets
    stt_provider = db.Column(db.String(20), default="whisper")
    email_sender = db.Column(db.String(200))
    email_password = db.Column(db.String(200))   # encrypted in production
```

> **Storage Backend Logic:** When `storage_backend == "database"`, the Output & Storage module writes meeting data to the `Meeting` table. When `storage_backend == "google_sheets"`, it writes to Google Sheets instead. The Meeting model always stores a local copy for the history page regardless.

### 4.1 Module 1: Meeting Access (`modules/meeting_access.py`)

**Purpose:** Automatically join a virtual meeting link using Selenium browser automation.

#### Key Functions

| Function                     | Description                                                      |
|------------------------------|------------------------------------------------------------------|
| `init_browser()`             | Initialise Chrome/Edge with required options (mute mic/cam).     |
| `join_meeting(link)`         | Navigate to meeting URL and handle the join flow.                |
| `handle_waiting_room()`      | Wait for host admission if applicable.                           |
| `stay_connected(duration)`   | Keep the browser alive for the meeting duration.                 |
| `leave_meeting()`            | Gracefully close the meeting and browser.                        |
| `detect_platform(link)`      | Detect if the link is Zoom, Google Meet, or Teams.               |

#### Implementation Notes

```python
# Selenium browser configuration
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def init_browser():
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--use-fake-ui-for-media-stream")  # Auto-allow mic/cam prompts
    options.add_argument("--use-fake-device-for-media-stream")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver
```

#### Platform-Specific Join Logic

| Platform     | Join Strategy                                                                   |
|--------------|---------------------------------------------------------------------------------|
| Google Meet  | Navigate to link → dismiss pre-join dialog → click "Join now" button.           |
| Zoom (Web)   | Navigate to web client link → enter name → click "Join" → handle waiting room.  |
| MS Teams     | Navigate to link → select "Continue on this browser" → click "Join now".        |

> **⚠ Risk:** Platform UI changes may break CSS selectors. Selectors should be stored in a configuration file for easy updates.

---

### 4.2 Module 2: Audio Capture (`modules/audio_capture.py`)

**Purpose:** Control OBS Studio via WebSocket to record system audio during the meeting.

#### Key Functions

| Function                     | Description                                                      |
|------------------------------|------------------------------------------------------------------|
| `connect_obs()`              | Establish WebSocket connection to OBS.                           |
| `start_recording()`          | Send start-recording command to OBS.                             |
| `stop_recording()`           | Send stop-recording command to OBS.                              |
| `check_recording_status()`   | Poll OBS for current recording state.                            |
| `get_output_path()`          | Return the file path of the recorded audio.                      |
| `healthcheck()`              | Verify OBS is running and WebSocket is responsive.               |

#### Implementation Notes

```python
import obsws_python as obs

def connect_obs(host="localhost", port=4455, password=""):
    """Establish connection to OBS WebSocket."""
    client = obs.ReqClient(host=host, port=port, password=password)
    return client

def start_recording(client):
    """Start OBS recording."""
    client.start_record()

def stop_recording(client):
    """Stop OBS recording and return output path."""
    client.stop_record()
    response = client.get_last_replay_buffer_replay()
    return response
```

#### OBS Configuration Requirements

| Setting              | Value                                         |
|----------------------|-----------------------------------------------|
| Output Format        | `.wav` or `.mp3` (configurable)               |
| Audio Source         | Desktop Audio / System Audio                  |
| WebSocket Port       | `4455` (default)                              |
| WebSocket Password   | Stored in `.env`                              |
| Output Directory     | `./recordings/`                               |

#### Pre-flight Checklist (automated)
1. ✅ OBS is running.
2. ✅ WebSocket plugin is enabled and reachable.
3. ✅ Audio source is correctly mapped.
4. ✅ Output directory exists and is writable.

---

### 4.3 Module 3: Transcription (`modules/transcription.py`)

**Purpose:** Send recorded audio to an external STT API and receive the transcription.

#### Key Functions

| Function                              | Description                                           |
|---------------------------------------|-------------------------------------------------------|
| `transcribe_audio(file_path, provider)` | Route audio to the selected STT provider.           |
| `transcribe_whisper(file_path)`       | Transcribe using OpenAI Whisper API.                  |
| `transcribe_deepgram(file_path)`      | Transcribe using Deepgram API.                        |
| `transcribe_assemblyai(file_path)`    | Transcribe using AssemblyAI API.                      |
| `normalise_output(raw_response)`      | Normalise all provider responses to a unified format. |
| `get_diarisation(raw_response)`       | Extract speaker diarisation data if available.        |

#### Unified Transcription Format

```python
# Internal normalised format for all providers
{
    "full_text": "Complete transcription text...",
    "segments": [
        {
            "speaker": "Speaker 1",       # if diarisation available
            "start_time": 0.0,
            "end_time": 12.5,
            "text": "Hello everyone, let's begin..."
        }
    ],
    "language": "en",
    "duration_seconds": 1800,
    "provider": "whisper",
    "diarisation_available": True
}
```

#### Provider Comparison

| Feature          | Whisper API        | Deepgram           | AssemblyAI         |
|------------------|--------------------|--------------------|--------------------|
| Accuracy         | ⭐⭐⭐⭐⭐              | ⭐⭐⭐⭐               | ⭐⭐⭐⭐               |
| Speed            | ⭐⭐⭐                | ⭐⭐⭐⭐⭐              | ⭐⭐⭐⭐               |
| Diarisation      | ❌ (needs workaround)| ✅                  | ✅                  |
| Cost             | $0.006/min         | $0.0043/min        | $0.00025/sec       |
| Streaming        | ❌                  | ✅                  | ✅                  |

> **Default Provider:** Whisper API — selected for reliability and accuracy.

---

### 4.4 Module 4: Summarisation & Analysis (`modules/summarisation.py`)

**Purpose:** Generate structured meeting summaries and participation analysis using an LLM.

#### Key Functions

| Function                             | Description                                            |
|--------------------------------------|--------------------------------------------------------|
| `generate_summary(transcript)`       | Produce a structured meeting summary.                  |
| `extract_action_items(transcript)`   | Extract assigned tasks and deadlines.                  |
| `extract_decisions(transcript)`      | Extract key decisions made during the meeting.         |
| `analyse_participation(segments)`    | Compute speaker statistics from diarisation data.      |
| `build_report(summary, analysis)`    | Combine all outputs into a final meeting report.       |

#### Summary Prompt Template

```python
SUMMARY_PROMPT = """
You are an AI meeting assistant. Analyse the following meeting transcript 
and produce a structured summary.

**Output Format:**
1. **Meeting Overview** — A 2-3 sentence summary of the meeting's purpose and outcome.
2. **Key Discussion Points** — Bullet list of the main topics discussed.
3. **Decisions Made** — List of decisions with context.
4. **Action Items** — Table format: | Assignee | Task | Deadline |
5. **Follow-Up Required** — Any unresolved items that need future attention.

**Transcript:**
{transcript}
"""
```

#### Participation Analysis Output

```python
# When diarisation data is available
{
    "speaker_stats": [
        {
            "speaker": "Speaker 1",
            "total_speaking_time_sec": 540,
            "percentage_of_meeting": 30.0,
            "number_of_turns": 25
        },
        {
            "speaker": "Speaker 2",
            "total_speaking_time_sec": 360,
            "percentage_of_meeting": 20.0,
            "number_of_turns": 18
        }
    ],
    "most_active_speaker": "Speaker 1",
    "total_meeting_duration_sec": 1800
}
```

---

### 4.5 Module 5: Output & Storage (`modules/output_storage.py`)

**Purpose:** Deliver the final report and archive all data.

#### Key Functions

| Function                                   | Description                                           |
|--------------------------------------------|-------------------------------------------------------|
| `send_email(recipients, subject, body)`    | Send the meeting summary via email.                   |
| `format_email_body(report)`               | Convert the report into an HTML email format.         |
| `store_to_sheets(data, spreadsheet_id)`   | Write meeting data to Google Sheets.                  |
| `store_to_database(data)`                 | (Alternative) Store data in SQLite/PostgreSQL.        |
| `log_session(session_data)`               | Record session metadata for auditing.                 |

#### Email Configuration

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(recipients, subject, body, sender_email, sender_password):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    
    html_part = MIMEText(body, "html")
    msg.attach(html_part)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())
```

#### Google Sheets Schema

| Column          | Description                          |
|-----------------|--------------------------------------|
| Meeting Date    | Date and time of the meeting.        |
| Meeting Link    | Original meeting URL.                |
| Duration        | Total meeting duration in minutes.   |
| Participants    | List of attendees.                   |
| Summary         | Generated meeting summary.           |
| Action Items    | Extracted tasks and assignments.      |
| Decisions       | Key decisions made.                  |
| Transcript Link | Link to full transcript file.        |
| Status          | Processing status (Success/Failed).  |

---

## 5. Configuration Management

### `.env` File Structure

```env
# === App Configuration ===
SECRET_KEY=your_flask_secret_key
DATABASE_URI=sqlite:///meetings.db         # or postgresql://user:pass@host/dbname
STORAGE_BACKEND=database                   # database | google_sheets (default, overridden by Settings page)

# === STT API Keys ===
WHISPER_API_KEY=sk-...
DEEPGRAM_API_KEY=dg-...
ASSEMBLYAI_API_KEY=aa-...
STT_PROVIDER=whisper                    # whisper | deepgram | assemblyai

# === LLM Configuration ===
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4                        # Model for summarisation

# === OBS Configuration ===
OBS_WEBSOCKET_HOST=localhost
OBS_WEBSOCKET_PORT=4455
OBS_WEBSOCKET_PASSWORD=your_password

# === Email Configuration ===
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=465

# === Google Sheets ===
GOOGLE_SHEETS_CRED_FILE=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# === Paths ===
RECORDINGS_DIR=./recordings
TRANSCRIPTS_DIR=./transcripts
SUMMARIES_DIR=./summaries
LOGS_DIR=./logs
```

### `config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # App
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///meetings.db")
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "database")  # database | google_sheets
    
    # STT
    STT_PROVIDER = os.getenv("STT_PROVIDER", "whisper")
    WHISPER_API_KEY = os.getenv("WHISPER_API_KEY")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
    
    # LLM
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
    
    # OBS
    OBS_HOST = os.getenv("OBS_WEBSOCKET_HOST", "localhost")
    OBS_PORT = int(os.getenv("OBS_WEBSOCKET_PORT", 4455))
    OBS_PASSWORD = os.getenv("OBS_WEBSOCKET_PASSWORD", "")
    
    # Email
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    
    # Google Sheets
    SHEETS_CRED_FILE = os.getenv("GOOGLE_SHEETS_CRED_FILE", "credentials.json")
    SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    
    # Paths
    RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "./recordings")
    TRANSCRIPTS_DIR = os.getenv("TRANSCRIPTS_DIR", "./transcripts")
    SUMMARIES_DIR = os.getenv("SUMMARIES_DIR", "./summaries")
    LOGS_DIR = os.getenv("LOGS_DIR", "./logs")
```

---

## 6. Main Pipeline (`main.py`)

```python
"""
AI Meeting Assistant — Pipeline Orchestrator
=============================================
Called from app.py web routes to process a meeting.
Runs as a background thread per meeting session.
"""

import sys
import logging
from datetime import datetime
from config import Config
from models import db, Meeting
from modules.meeting_access import MeetingAccess
from modules.audio_capture import AudioCapture
from modules.transcription import Transcription
from modules.summarisation import Summarisation
from modules.output_storage import OutputStorage
from utils.logger import setup_logger

def run_pipeline(meeting_link: str, participant_emails: list[str], storage_backend: str = "database"):
    """Full meeting pipeline — triggered by the dashboard."""
    logger = setup_logger()
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"=== Session {session_id} started ===")
    
    # Create meeting record in DB (for history page tracking)
    meeting_record = Meeting(
        session_id=session_id,
        meeting_link=meeting_link,
        participants=", ".join(participant_emails),
        status="joining",
        storage_backend=storage_backend
    )
    # Note: db.session operations here require app context
    
    try:
        # ── Step 1: Join Meeting ──
        logger.info("Step 1: Joining meeting...")
        meeting_record.status = "joining"
        meeting = MeetingAccess()
        meeting.join(meeting_link)
        meeting_record.platform = meeting.detected_platform
        logger.info("Successfully joined the meeting.")
        
        # ── Step 2: Start Recording ──
        logger.info("Step 2: Starting audio recording...")
        meeting_record.status = "recording"
        recorder = AudioCapture()
        recorder.start()
        logger.info("Recording started.")
        
        # ── Step 3: Wait for Meeting to End ──
        logger.info("Step 3: Waiting for meeting to end...")
        meeting.wait_until_end()
        
        # ── Step 4: Stop Recording ──
        logger.info("Step 4: Stopping recording...")
        audio_file = recorder.stop()
        meeting_record.audio_file_path = audio_file
        logger.info(f"Audio saved: {audio_file}")
        
        # ── Step 5: Transcribe ──
        logger.info("Step 5: Transcribing audio...")
        meeting_record.status = "transcribing"
        transcriber = Transcription(provider=Config.STT_PROVIDER)
        transcript = transcriber.transcribe(audio_file)
        meeting_record.transcript = transcript["full_text"]
        logger.info("Transcription complete.")
        
        # ── Step 6: Summarise ──
        logger.info("Step 6: Generating summary...")
        meeting_record.status = "summarising"
        summariser = Summarisation()
        report = summariser.generate_report(transcript)
        meeting_record.summary = report["summary"]
        meeting_record.action_items = str(report.get("action_items", []))
        meeting_record.decisions = str(report.get("decisions", []))
        logger.info("Summary generated.")
        
        # ── Step 7: Deliver & Store ──
        logger.info("Step 7: Sending emails and storing data...")
        meeting_record.status = "delivering"
        output = OutputStorage(backend=storage_backend)
        output.send_email(participant_emails, report)
        output.store(report, transcript)
        logger.info("Emails sent and data stored successfully.")
        
        meeting_record.status = "completed"
        logger.info(f"=== Session {session_id} completed ===")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        meeting_record.status = "failed"
    finally:
        meeting.leave()
```

---

## 7. Error Handling Strategy

| Error Scenario                    | Detection                      | Fallback Action                              |
|-----------------------------------|--------------------------------|----------------------------------------------|
| Failed to join meeting            | Selenium timeout               | Retry 3 times with 10s delay, then abort.    |
| OBS WebSocket not reachable       | Connection refused             | Log error; prompt user to check OBS.         |
| OBS recording interrupted         | Status poll returns idle       | Attempt restart; log partial recording.      |
| STT API timeout                   | HTTP 408 / connection timeout  | Retry with exponential backoff (3 attempts). |
| STT API rate limit                | HTTP 429                       | Switch to fallback STT provider.             |
| LLM summarisation failure         | API error                      | Retry; fallback to basic extractive summary. |
| Email delivery failure            | SMTP error                     | Retry; log failed recipients for manual send.|
| Google Sheets write failure       | API error                      | Fallback to local JSON/CSV file.             |

---

## 8. Logging Strategy

### Log Levels

| Level    | Usage                                                     |
|----------|-----------------------------------------------------------|
| DEBUG    | Detailed diagnostic info (API payloads, timing data).     |
| INFO     | Standard pipeline progress (step started/completed).      |
| WARNING  | Non-critical issues (retry attempts, fallback activations).|
| ERROR    | Errors that halt a specific step.                         |
| CRITICAL | Errors that abort the entire pipeline.                    |

### Log Format

```
[2026-03-12 14:30:15] [INFO] [meeting_access] Step 1: Joining meeting - https://meet.google.com/abc-defg-hij
[2026-03-12 14:30:22] [INFO] [meeting_access] Successfully joined the meeting.
[2026-03-12 14:30:23] [INFO] [audio_capture] Step 2: Starting OBS recording...
[2026-03-12 15:01:05] [INFO] [audio_capture] Recording stopped. File: ./recordings/20260312_143015.wav
[2026-03-12 15:01:10] [INFO] [transcription] Step 5: Sending to Whisper API...
[2026-03-12 15:04:32] [INFO] [transcription] Transcription complete. Duration: 3m22s.
```

### Session Log File

Each meeting session produces a structured log at `./logs/session_{session_id}.json`:

```json
{
    "session_id": "20260312_143015",
    "meeting_link": "https://meet.google.com/abc-defg-hij",
    "platform": "google_meet",
    "join_time": "2026-03-12T14:30:22",
    "leave_time": "2026-03-12T15:01:03",
    "recording_duration_sec": 1841,
    "audio_file": "./recordings/20260312_143015.wav",
    "stt_provider": "whisper",
    "transcription_time_sec": 202,
    "summary_generated": true,
    "emails_sent": ["alice@example.com", "bob@example.com"],
    "emails_failed": [],
    "storage_status": "success",
    "errors": []
}
```

---

## 9. Implementation Phases

### Phase 0: Frontend Dashboard — TDD (Week 1)

| # | TDD Step                                                       | Deliverable                           |
|---|----------------------------------------------------------------|---------------------------------------|
| 1 | **🔴 Red:** Write `tests/conftest.py` with shared fixtures.    | Test fixtures (test client, test DB). |
| 2 | **🔴 Red:** Write `tests/test_models.py` for Meeting & Settings models. | Failing model tests.          |
| 3 | **🟢 Green:** Implement `models.py` to pass model tests.      | `Meeting` and `Settings` models.      |
| 4 | **🔴 Red:** Write `tests/test_dashboard.py` for all routes.   | Failing route tests.                  |
| 5 | **🟢 Green:** Implement `app.py` and all templates.            | Working Flask app + templates.        |
| 6 | **🔵 Refactor:** Clean up code, add CSS styling.               | `style.css`, clean app structure.     |
| 7 | **Coverage check:** Run `pytest --cov` — target ≥ 80%.         | Coverage report.                      |

### Phase 1: Foundation & Meeting Access — TDD (Week 2–3)

| # | TDD Step                                                        | Deliverable                           |
|---|----------------------------------------------------------------|---------------------------------------|
| 1 | **🔴 Red:** Write `tests/test_config.py` for Config loading.   | Failing config tests.                 |
| 2 | **🟢 Green:** Implement `config.py` and `.env` handling.       | Centralised configuration.            |
| 3 | **🔴 Red:** Write `tests/test_logger.py` for logger setup.     | Failing logger tests.                 |
| 4 | **🟢 Green:** Implement `utils/logger.py`.                     | Logging utility.                      |
| 5 | **🔴 Red:** Write `tests/test_meeting_access.py` — platform detection, join, leave. | Failing meeting access tests. |
| 6 | **🟢 Green:** Implement `modules/meeting_access.py`.           | Selenium-based meeting joiner.        |
| 7 | **🔵 Refactor:** Extract selectors to config, improve retries. | Clean, configurable module.           |
| 8 | **Coverage check:** Run `pytest --cov` — target ≥ 75%.         | Coverage report.                      |

### Phase 2: Audio Capture — TDD (Week 3–4)

| # | TDD Step                                                       | Deliverable                          |
|---|----------------------------------------------------------------|--------------------------------------|
| 1 | **🔴 Red:** Write `tests/test_audio_capture.py` — connect, start, stop, healthcheck. | Failing audio capture tests. |
| 2 | **🟢 Green:** Implement `modules/audio_capture.py`.            | OBS WebSocket controller.            |
| 3 | **🔵 Refactor:** Improve error handling, add pre-flight checks.| Robust audio capture module.         |
| 4 | **Integration test:** Selenium + OBS (mocked) end-to-end.      | Verified join + record pipeline.     |
| 5 | **Coverage check:** Run `pytest --cov` — target ≥ 75%.         | Coverage report.                     |

### Phase 3: Transcription — TDD (Week 4–5)

| # | TDD Step                                                       | Deliverable                          |
|---|----------------------------------------------------------------|--------------------------------------|
| 1 | **🔴 Red:** Write `tests/test_transcription.py` — all providers, normalisation, retries. | Failing transcription tests. |
| 2 | **🟢 Green:** Implement Whisper API integration.               | Primary STT module.                  |
| 3 | **🟢 Green:** Implement Deepgram and AssemblyAI integrations.  | Alternative STT providers.           |
| 4 | **🟢 Green:** Implement unified output normalisation.          | Standardised transcript format.      |
| 5 | **🔵 Refactor:** Unify retry logic, improve error handling.    | Clean, provider-agnostic module.     |
| 6 | **Coverage check:** Run `pytest --cov` — target ≥ 80%.         | Coverage report.                     |

### Phase 4: Summarisation & Analysis — TDD (Week 5–6)

| # | TDD Step                                                       | Deliverable                          |
|---|----------------------------------------------------------------|--------------------------------------|
| 1 | **🔴 Red:** Write `tests/test_summarisation.py` — summary, action items, decisions, participation. | Failing summarisation tests. |
| 2 | **🟢 Green:** Implement LLM-based summarisation.               | Summary generator.                   |
| 3 | **🟢 Green:** Implement action item and decision extraction.   | Structured report components.        |
| 4 | **🟢 Green:** Implement participation analysis.                | Speaker statistics module.           |
| 5 | **🔵 Refactor:** Improve prompt templates, optimise parsing.   | Clean, well-structured module.       |
| 6 | **Coverage check:** Run `pytest --cov` — target ≥ 80%.         | Coverage report.                     |

### Phase 5: Output & Storage — TDD (Week 6–7)

| # | TDD Step                                                       | Deliverable                          |
|---|----------------------------------------------------------------|--------------------------------------|
| 1 | **🔴 Red:** Write `tests/test_output_storage.py` — email, DB, Sheets, fallback. | Failing output/storage tests. |
| 2 | **🟢 Green:** Implement email delivery via SMTP.               | Email sender module.                 |
| 3 | **🟢 Green:** Implement Google Sheets integration.             | Sheets storage module.               |
| 4 | **🟢 Green:** Implement database storage via SQLAlchemy.       | Database storage module.             |
| 5 | **🟢 Green:** Implement storage router (DB vs Sheets).         | Configurable storage backend.        |
| 6 | **🔴 Red:** Write `tests/test_pipeline.py` — happy path, failures, status tracking. | Failing pipeline tests. |
| 7 | **🟢 Green:** Build `main.py` pipeline orchestration.          | Complete end-to-end pipeline.        |
| 8 | **🔵 Refactor:** Clean up all modules, ensure consistent patterns. | Polished codebase.              |
| 9 | **Coverage check:** Run `pytest --cov` — target ≥ 80%.         | Coverage report.                     |

### Phase 6: Integration & Final Testing (Week 7–8)

| # | TDD Step                                                       | Deliverable                          |
|---|----------------------------------------------------------------|--------------------------------------|
| 1 | Integrate dashboard with backend pipeline.                     | End-to-end web workflow.             |
| 2 | Run full test suite — all tests must pass.                     | Green test suite.                    |
| 3 | Run `pytest --cov` — overall coverage ≥ 80%.                   | Final coverage report.               |
| 4 | Error handling hardening and edge case testing.                | Robust error recovery.               |
| 5 | Final documentation and README.                                | Complete project documentation.      |

---

## 10. Testing Strategy — Test-Driven Development (TDD)

> **Core Principle:** Every feature is developed using the **Red → Green → Refactor** cycle. No production code is written without a failing test first.

### 10.1 TDD Development Workflow

For every feature in the implementation:

```
1. 🔴 RED:      Write a failing test that defines expected behaviour.
2. 🟢 GREEN:    Write the MINIMUM code to make the test pass.
3. 🔵 REFACTOR: Improve code quality. Run pytest — all tests must still pass.
4. ↺ REPEAT:    Move to the next feature.
```

### 10.2 Test Execution Order (by Phase)

| Phase | Tests Written First              | Then Implement                              |
|-------|----------------------------------|---------------------------------------------|
| 0     | `test_models.py`, `test_dashboard.py` | `models.py`, `app.py`, templates       |
| 1     | `test_config.py`, `test_logger.py`, `test_meeting_access.py` | `config.py`, `logger.py`, `meeting_access.py` |
| 2     | `test_audio_capture.py`          | `audio_capture.py`                          |
| 3     | `test_transcription.py`          | `transcription.py`                          |
| 4     | `test_summarisation.py`          | `summarisation.py`                          |
| 5     | `test_output_storage.py`, `test_pipeline.py` | `output_storage.py`, `main.py`     |
| 6     | Full regression + integration    | Bug fixes, hardening                        |

### 10.3 Unit Testing (TDD)

| Module                | Tests Written First                                       |
|-----------------------|-----------------------------------------------------------|
| `models.py`           | Model creation, default values, status lifecycle, CRUD.   |
| `app.py` (dashboard)  | Route responses, form validation, template rendering.     |
| `config.py`           | Default loading, env override, type parsing.              |
| `meeting_access.py`   | Platform detection, browser init (mocked), join/leave.    |
| `audio_capture.py`    | OBS connect (mocked), start/stop, healthcheck.            |
| `transcription.py`    | API request formatting (mocked), response normalisation.  |
| `summarisation.py`    | Prompt construction, output parsing (mocked), analysis.   |
| `output_storage.py`   | Email formatting (mocked), Sheets write, DB write.        |

### 10.4 Integration Testing

| Integration           | Test Scenario                                             |
|-----------------------|-----------------------------------------------------------|
| Dashboard → Pipeline  | Submit form → pipeline starts → status updates.          |
| Selenium + OBS        | Join meeting → start recording → stop recording (mocked).|
| OBS + STT API         | Record audio → send to API → receive transcription.      |
| STT + Summariser      | Transcription → generate summary → extract action items. |
| Summariser + Output   | Generate report → send email → store in selected backend.|
| Settings → Storage    | Toggle DB/Sheets → confirm data routes correctly.        |

### 10.5 System Testing

- Full end-to-end pipeline test with a real meeting.
- Test with different meeting platforms (Zoom, Meet, Teams).
- Test with different audio quality levels.

### 10.6 Performance Testing

| Metric                | Test Method                            | Target           |
|-----------------------|----------------------------------------|------------------|
| Audio recording       | Record 30-min meeting; verify file     | Complete file     |
| Transcription speed   | Time API round-trip for 30-min audio   | < 5 min           |
| Summary generation    | Time LLM processing                   | < 2 min           |
| Total pipeline        | End-to-end timing                      | < 10 min          |

### 10.7 Coverage Targets

| Module                       | Minimum | Target |
|------------------------------|---------|--------|
| `app.py`                     | 80%     | 90%    |
| `models.py`                  | 90%     | 100%   |
| `config.py`                  | 90%     | 100%   |
| `modules/meeting_access.py`  | 75%     | 85%    |
| `modules/audio_capture.py`   | 75%     | 85%    |
| `modules/transcription.py`   | 80%     | 90%    |
| `modules/summarisation.py`   | 80%     | 90%    |
| `modules/output_storage.py`  | 80%     | 90%    |
| `main.py`                    | 75%     | 85%    |
| **Overall**                  | **80%** | **90%**|

### 10.8 Running Tests

```bash
# TDD cycle — run frequently during development
python -m pytest tests/ -v

# Run specific module tests
python -m pytest tests/test_transcription.py -v

# Run with coverage
python -m pytest tests/ --cov=modules --cov=. --cov-report=html --cov-report=term-missing

# Run only previously failing tests (fast feedback)
python -m pytest tests/ --lf -v

# Run tests matching a keyword
python -m pytest tests/ -k "platform" -v
```

---

## 11. Deployment & Usage

### 11.1 Installation

```bash
# 1. Clone repository
git clone <repository_url>
cd ai-meeting-assistant

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys and credentials

# 5. Configure OBS Studio
# - Enable WebSocket in OBS → Tools → WebSocket Server Settings
# - Set the same password as in .env
# - Add "Desktop Audio" as an audio input source
```

### 11.2 Running the System

```bash
# Start the web dashboard
python app.py

# Open in browser: http://localhost:5000
# 1. Go to Settings → choose storage backend (Database or Google Sheets)
# 2. Go to Dashboard → enter meeting link + participant emails → click "Join Meeting"
# 3. Go to History → view processed meetings and their summaries
```

---

## 12. Future Enhancements

| Enhancement                          | Description                                                    | Priority   |
|--------------------------------------|----------------------------------------------------------------|------------|
| Real-time transcription              | Stream-based STT for live captioning during meetings.         | Medium     |
| Sentiment analysis                   | Detect participant tone using NLP.                            | Medium     |
| Multi-language support               | Handle meetings in multiple languages.                        | Low        |
| Calendar integration                 | Auto-detect meetings from Google Calendar.                    | High       |
| Slack/Teams notification             | Post summaries to team channels instead of email only.        | Medium     |
| Meeting recording from cloud         | Use platform APIs to fetch cloud recordings (no OBS needed).  | High       |
| User authentication                  | Login/registration for multi-user dashboard access.           | Medium     |
| Dark mode UI                         | Add dark mode toggle to the dashboard.                        | Low        |
