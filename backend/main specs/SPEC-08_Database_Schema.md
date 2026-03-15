# SPEC-08: Database Schema (MongoDB + Beanie ODM)

| Field            | Details                                       |
|------------------|-----------------------------------------------|
| **Database**     | MongoDB 7.x                                   |
| **Driver**       | Motor 3.x (async MongoDB driver for Python)   |
| **ODM**          | Beanie 1.x (async ODM, built on Motor + Pydantic) |
| **File**         | `models.py`                                   |
| **Version**      | 1.0                                           |
| **Date**         | March 12, 2026                                |

---

## 08.0 Why Beanie?

| Criteria               | Beanie                                 | MongoEngine                  | ODMantic                     |
|------------------------|----------------------------------------|------------------------------|------------------------------|
| Async support          | ✅ Native (built on Motor)             | ❌ Synchronous only          | ✅ Async (via Motor)         |
| Pydantic integration   | ✅ Models ARE Pydantic BaseModels      | ❌ Custom field system       | ✅ Pydantic v2              |
| FastAPI compatibility  | ✅ Seamless (shared Pydantic models)   | ⚠️ Requires serialisation   | ✅ Good                      |
| Migrations             | ✅ Built-in migration support          | ❌ Limited                   | ❌ None                      |
| Community & maintenance| ✅ Active                              | ✅ Mature                    | ⚠️ Smaller community        |

**Decision:** Beanie is chosen because:
1. Models are Pydantic `BaseModel` subclasses → FastAPI can use them directly as request/response schemas.
2. Fully async → matches FastAPI's async architecture.
3. Built on Motor → production-grade async MongoDB driver.

---

## 08.1 Database Initialisation

```python
# database.py
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from models import Meeting, Settings

async def init_db():
    """Initialise MongoDB connection and Beanie ODM."""
    client = AsyncIOMotorClient(Config.MONGODB_URI)
    await init_beanie(
        database=client[Config.MONGODB_DATABASE],
        document_models=[Meeting, Settings]
    )
```

Called at FastAPI startup:

```python
# app.py
from fastapi import FastAPI
from database import init_db

app = FastAPI(title="AI Meeting Assistant API")

@app.on_event("startup")
async def startup():
    await init_db()
```

---

## 08.2 Meeting Collection

**Collection name:** `meetings`

### Beanie Document Model

```python
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional
from enum import Enum

class MeetingStatus(str, Enum):
    PENDING = "pending"
    JOINING = "joining"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    SUMMARISING = "summarising"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    FAILED = "failed"

class ActionItem(BaseModel):
    assignee: str
    task: str
    deadline: Optional[str] = None

class SpeakerInfo(BaseModel):
    speaker: str
    total_speaking_time_sec: float
    percentage_of_meeting: float
    number_of_turns: int

class SpeakerStats(BaseModel):
    speakers: list[SpeakerInfo]
    most_active_speaker: str
    total_meeting_duration_sec: float

class Meeting(Document):
    session_id: str                                     # Unique timestamp-based ID
    meeting_link: str                                   # Original meeting URL
    platform: Optional[str] = None                      # "google_meet" | "zoom" | "teams"
    date: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: Optional[int] = None
    participants: list[str] = []                        # Array of email strings
    transcript: Optional[str] = None                    # Full transcription text
    summary: Optional[str] = None                       # Generated summary (markdown)
    action_items: list[ActionItem] = []                 # Embedded action items
    decisions: list[str] = []                           # Embedded decisions list
    speaker_stats: Optional[SpeakerStats] = None        # Embedded speaker statistics
    status: MeetingStatus = MeetingStatus.PENDING
    audio_file_path: Optional[str] = None               # Path to recorded audio file
    storage_backend: Optional[str] = None               # "database" | "google_sheets"
    failure_reason: Optional[str] = None                # Reason for failure (if failed)

    class Settings:
        name = "meetings"                               # MongoDB collection name
        indexes = [
            "session_id",                               # Unique index for lookups
            "status",                                   # Filter by pipeline status
            [("date", -1)],                             # Sort by date descending
        ]
```

### Document Schema (MongoDB)

```json
{
    "_id": ObjectId("..."),
    "session_id": "20260312_143015",
    "meeting_link": "https://meet.google.com/abc-defg-hij",
    "platform": "google_meet",
    "date": ISODate("2026-03-12T14:30:15Z"),
    "duration_minutes": 31,
    "participants": ["alice@example.com", "bob@example.com"],
    "transcript": "Full transcription text...",
    "summary": "## Meeting Overview\n...",
    "action_items": [
        {"assignee": "Alice", "task": "Review design mockups", "deadline": "2026-03-15"},
        {"assignee": "Bob", "task": "Update API docs", "deadline": null}
    ],
    "decisions": [
        "Approved the new UI design",
        "Postponed database migration to next sprint"
    ],
    "speaker_stats": {
        "speakers": [
            {"speaker": "Speaker 1", "total_speaking_time_sec": 620, "percentage_of_meeting": 55.2, "number_of_turns": 23},
            {"speaker": "Speaker 2", "total_speaking_time_sec": 504, "percentage_of_meeting": 44.8, "number_of_turns": 19}
        ],
        "most_active_speaker": "Speaker 1",
        "total_meeting_duration_sec": 1124
    },
    "status": "completed",
    "audio_file_path": "./recordings/20260312_143015.wav",
    "storage_backend": "database",
    "failure_reason": null
}
```

### Common Queries

```python
# Get all meetings sorted by date (newest first)
meetings = await Meeting.find_all().sort("-date").to_list()

# Get a meeting by ID
meeting = await Meeting.get(meeting_id)

# Get a meeting by session_id
meeting = await Meeting.find_one(Meeting.session_id == session_id)

# Update meeting status
meeting.status = MeetingStatus.RECORDING
await meeting.save()

# Update specific fields only
await meeting.set({Meeting.status: MeetingStatus.COMPLETED, Meeting.summary: summary_text})

# Get all failed meetings
failed = await Meeting.find(Meeting.status == MeetingStatus.FAILED).to_list()

# Count meetings by status
count = await Meeting.find(Meeting.status == MeetingStatus.COMPLETED).count()
```

**Status lifecycle:** `pending` → `joining` → `recording` → `transcribing` → `summarising` → `delivering` → `completed` | `failed`

---

## 08.3 Settings Collection

**Collection name:** `settings`

### Beanie Document Model

```python
class Settings(Document):
    storage_backend: str = "database"               # "database" | "google_sheets"
    stt_provider: str = "whisper"                    # "whisper" | "deepgram" | "assemblyai"
    email_sender: Optional[str] = None
    email_password: Optional[str] = None

    class Settings:
        name = "settings"                            # MongoDB collection name
```

> **Singleton pattern:** Only one `Settings` document exists. Retrieved via `await Settings.find_one()`, created with defaults if not found.

### Get-or-create Helper

```python
async def get_settings() -> Settings:
    """Retrieve the singleton settings document, creating defaults if none exists."""
    settings = await Settings.find_one()
    if settings is None:
        settings = Settings()
        await settings.insert()
    return settings
```

---

## 08.4 Indexes

| Collection  | Index                | Type     | Purpose                           |
|-------------|----------------------|----------|-----------------------------------|
| `meetings`  | `session_id`         | Unique   | Fast lookup by session ID         |
| `meetings`  | `status`             | Standard | Filter meetings by pipeline state |
| `meetings`  | `date` (descending)  | Standard | History page sort order           |

Indexes are created automatically by Beanie on startup via the `Settings.indexes` configuration.

---

## 08.5 Data Migration Notes

- MongoDB is **schemaless** — no migrations are needed for adding new fields.
- New fields added to the Beanie model will default to `None` (or specified default) for existing documents.
- Beanie supports `@before_event` and `@after_event` hooks for data transformations.

---

## 08.6 Acceptance Criteria

| #  | Criteria                                                                    | Verified |
|----|-----------------------------------------------------------------------------|----------|
| 1  | MongoDB connection established on FastAPI startup via `init_db()`.         | ☐        |
| 2  | `meetings` collection created automatically with correct indexes.          | ☐        |
| 3  | `settings` collection initialised with default values if empty.            | ☐        |
| 4  | Meeting documents store `action_items` and `decisions` as embedded arrays. | ☐        |
| 5  | All Beanie queries are fully async (no blocking calls).                    | ☐        |
