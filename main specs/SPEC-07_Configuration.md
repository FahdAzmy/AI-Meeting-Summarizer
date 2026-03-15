# SPEC-07: Configuration & Environment

| Field            | Details                                       |
|------------------|-----------------------------------------------|
| **File**         | `config.py` + `.env`                          |
| **Class**        | `Config` (Pydantic `BaseSettings`)            |
| **Framework**    | FastAPI + Pydantic Settings                   |
| **Version**      | 1.0                                           |
| **Date**         | March 12, 2026                                |

---

## 07.1 Configuration Class (Pydantic BaseSettings)

FastAPI uses Pydantic `BaseSettings` for type-safe, validated configuration:

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Config(BaseSettings):
    # ── FastAPI ──
    APP_TITLE: str = "AI Meeting Assistant API"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    
    # ── MongoDB ──
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "meeting_assistant"
    
    # ── Storage ──
    STORAGE_BACKEND: str = "database"            # "database" | "google_sheets"
    
    # ── STT Providers ──
    STT_PROVIDER: str = "whisper"
    WHISPER_API_KEY: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None
    ASSEMBLYAI_API_KEY: Optional[str] = None
    
    # ── LLM ──
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"
    
    # ── OBS WebSocket ──
    OBS_WEBSOCKET_HOST: str = "localhost"
    OBS_WEBSOCKET_PORT: int = 4455
    OBS_WEBSOCKET_PASSWORD: str = ""
    
    # ── Email ──
    EMAIL_SENDER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    # ── Google Sheets ──
    GOOGLE_SHEETS_CRED_FILE: str = "credentials.json"
    GOOGLE_SHEETS_SPREADSHEET_ID: Optional[str] = None
    
    # ── Directories ──
    RECORDINGS_DIR: str = "./recordings"
    TRANSCRIPTS_DIR: str = "./transcripts"
    SUMMARIES_DIR: str = "./summaries"
    LOGS_DIR: str = "./logs"
    
    # ── CORS ──
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = Config()
```

---

## 07.2 Environment Variables

| Variable                       | Type     | Default                     | Description                           |
|--------------------------------|----------|-----------------------------|---------------------------------------|
| `APP_TITLE`                    | str      | `"AI Meeting Assistant API"`| FastAPI app title                     |
| `APP_HOST`                     | str      | `"0.0.0.0"`                | Server bind host                      |
| `APP_PORT`                     | int      | `8000`                      | Server bind port                      |
| `DEBUG`                        | bool     | `false`                     | Enable debug mode                     |
| `MONGODB_URI`                  | str      | `"mongodb://localhost:27017"` | MongoDB connection string           |
| `MONGODB_DATABASE`             | str      | `"meeting_assistant"`       | MongoDB database name                 |
| `STORAGE_BACKEND`              | str      | `"database"`                | Default storage (overridden by UI)    |
| `STT_PROVIDER`                 | str      | `"whisper"`                 | Default STT provider                  |
| `WHISPER_API_KEY`              | str      | —                           | OpenAI Whisper API key                |
| `DEEPGRAM_API_KEY`             | str      | —                           | Deepgram API key                      |
| `ASSEMBLYAI_API_KEY`           | str      | —                           | AssemblyAI API key                    |
| `OPENAI_API_KEY`               | str      | —                           | OpenAI LLM API key                    |
| `LLM_MODEL`                    | str      | `"gpt-4"`                  | LLM model name                        |
| `OBS_WEBSOCKET_HOST`           | str      | `"localhost"`               | OBS WebSocket host                    |
| `OBS_WEBSOCKET_PORT`           | int      | `4455`                      | OBS WebSocket port                    |
| `OBS_WEBSOCKET_PASSWORD`       | str      | `""`                        | OBS WebSocket password                |
| `EMAIL_SENDER`                 | str      | —                           | Sender email address                  |
| `EMAIL_PASSWORD`               | str      | —                           | Sender app password                   |
| `GOOGLE_SHEETS_CRED_FILE`      | str      | `"credentials.json"`       | Sheets service account key file       |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | str      | —                           | Target spreadsheet ID                 |
| `RECORDINGS_DIR`               | str      | `"./recordings"`            | Audio output directory                |
| `TRANSCRIPTS_DIR`              | str      | `"./transcripts"`           | Transcript output directory           |
| `SUMMARIES_DIR`                | str      | `"./summaries"`             | Summary output directory              |
| `LOGS_DIR`                     | str      | `"./logs"`                  | Log file directory                    |
| `CORS_ORIGINS`                 | list[str]| `["http://localhost:3000"]` | Allowed CORS origins (Next.js frontend) |

---

## 07.3 Example `.env` File

```env
# ── MongoDB ──
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=meeting_assistant

# ── API Keys ──
WHISPER_API_KEY=sk-...
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=
ASSEMBLYAI_API_KEY=

# ── OBS ──
OBS_WEBSOCKET_HOST=localhost
OBS_WEBSOCKET_PORT=4455
OBS_WEBSOCKET_PASSWORD=your_obs_password

# ── Email ──
EMAIL_SENDER=your.email@gmail.com
EMAIL_PASSWORD=your_app_password

# ── Google Sheets (optional) ──
GOOGLE_SHEETS_CRED_FILE=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=

# ── CORS ──
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 07.4 Settings Override Hierarchy

```
.env defaults  →  overridden by  →  Settings collection (user-configured via dashboard)
```

When the user changes a setting in the Settings page, it takes precedence over `.env` defaults for `storage_backend`, `stt_provider`, `email_sender`, and `email_password`.

The `get_settings()` helper (see SPEC-08) reads from MongoDB first; if a value is not set there, it falls back to `Config`.

---

## 07.5 Dependencies (`requirements.txt`)

```
# ── Framework ──
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
pydantic>=2.0
pydantic-settings>=2.0

# ── Database ──
motor>=3.3.0
beanie>=1.25.0

# ── Selenium ──
selenium>=4.15.0
webdriver-manager>=4.0.0

# ── OBS ──
obsws-python>=1.6.0

# ── Audio ──
pydub>=0.25.1

# ── STT APIs ──
openai>=1.10.0
deepgram-sdk>=3.0.0
assemblyai>=0.20.0

# ── LLM ──
# (uses openai package above)

# ── Google Sheets ──
gspread>=6.0.0
oauth2client>=4.1.3

# ── Email ──
aiosmtplib>=3.0.0

# ── Utilities ──
python-dotenv>=1.0.0
httpx>=0.27.0
```
