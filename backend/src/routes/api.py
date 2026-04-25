"""
src/routes/api.py
-----------------
REST API router for the AI Meeting Summariser backend.

Endpoints
---------
POST /trigger  — Launch the full AI pipeline as a background task (T016/T017).
POST /join     — Legacy endpoint for direct bot lifecycle management.
GET  /status   — Poll in-memory session status (legacy).
GET  /meetings — Meeting history placeholder.
"""

import time
import asyncio
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
import threading
from datetime import datetime
import uuid

from src.models.requests import JoinMeetingRequest, JoinMeetingResponse, StatusResponse

logger = logging.getLogger(__name__)

api_router = APIRouter()


# ---------------------------------------------------------------------------
# T016 / T017 — Pipeline trigger endpoint (Phase 6)
# ---------------------------------------------------------------------------


class TriggerRequest(BaseModel):
    """Request body for the ``POST /trigger`` endpoint.

    Attributes
    ----------
    meeting_link:
        URL of the meeting room to join (Zoom, Google Meet, Teams, …).
    emails:
        Recipient e-mail addresses for the final meeting report.
    storage:
        Storage backend identifier. Defaults to ``"email"``.
    """

    meeting_link: str = Field(
        ..., description="URL of the meeting to join.", examples=["https://meet.google.com/abc-defg-hij"]
    )
    emails: List[str] = Field(
        default_factory=list, description="Recipient e-mail addresses for the report."
    )
    storage: str = Field(
        default="email", description="Storage backend identifier (email, sheets, db)."
    )


class TriggerResponse(BaseModel):
    """Response body for the ``POST /trigger`` endpoint."""

    session_id: str = Field(
        ..., description="Unique session ID to track the pipeline status."
    )

    message: str = Field(
        ..., description="Human-readable confirmation message."
    )
    meeting_link: str = Field(
        ..., description="Echo of the submitted meeting link."
    )
    storage: str = Field(
        ..., description="Echo of the selected storage backend."
    )


@api_router.post("/trigger", response_model=TriggerResponse, status_code=202)
async def trigger_pipeline(
    request: TriggerRequest,
    background_tasks: BackgroundTasks,
):
    """Launch the full AI pipeline as a detached background task.

    The endpoint returns **immediately** with HTTP 202 (Accepted) while
    ``run_pipeline`` executes asynchronously via FastAPI's
    ``BackgroundTasks`` mechanism.  Pipeline progress is tracked via
    ``MeetingStatus`` mutations in MongoDB (see ``src/orchestrator.py``).
    """
    # Lazy import to avoid circular dependencies and to keep the module
    # importable even when heavy AI packages are not installed.
    from src.orchestrator import run_pipeline  # noqa: WPS433

    logger.info(
        "POST /trigger | link=%s | emails=%s | storage=%s",
        request.meeting_link,
        request.emails,
        request.storage,
    )

    # Generate a tracking session ID
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    background_tasks.add_task(
        run_pipeline,
        meeting_link=request.meeting_link,
        emails=request.emails,
        storage=request.storage,
        session_id=session_id,
    )

    return TriggerResponse(
        session_id=session_id,
        message="Pipeline launched successfully. Track progress via the dashboard.",
        meeting_link=request.meeting_link,
        storage=request.storage,
    )


# ---------------------------------------------------------------------------
# Legacy bot lifecycle (pre-orchestrator) — kept for backward compatibility
# ---------------------------------------------------------------------------

# In-memory "database" for statuses until the main Pipeline DB is connected
status_db: Dict[str, Dict[str, Any]] = {}


def bot_lifecycle_task(session_id: str, link: str):
    """
    Background worker that controls the Selenium Bot for this session.
    It updates the global status dictionary.
    """
    # Lazy import — only needed when this legacy path is used
    try:
        from modules.meeting_access import MeetingAccess
        from modules.errors import MeetingJoinError, PlatformNotSupported
    except ImportError:
        status_db[session_id] = {
            "status": "failed",
            "step": 0,
            "total_steps": 6,
            "message": "Meeting modules not installed.",
        }
        return

    status_db[session_id] = {
        "status": "joining",
        "step": 1,
        "total_steps": 6,
        "message": "Initializing browser and joining meeting..."
    }

    bot = None
    try:
        # Step 1: Initialize bot
        bot = MeetingAccess(headless=True)

        # Step 2: Join meeting
        bot.join(link)

        # Simulated recording phase
        status_db[session_id]["status"] = "recording"
        status_db[session_id]["step"] = 2
        status_db[session_id]["message"] = f"Connected to {bot.detected_platform}! Active listening mode..."

        # We simulate waiting for the meeting to end (it'll actually wait on the bot until max time or end)
        # Normally this loops until the meeting ends, but for demo we just sleep
        time.sleep(15)

        # We'd end the Meeting here
        status_db[session_id]["status"] = "completed"
        status_db[session_id]["step"] = 6
        status_db[session_id]["message"] = "Meeting concluded across all modules."

    except PlatformNotSupported as e:
        status_db[session_id]["status"] = "failed"
        status_db[session_id]["message"] = f"Unsupported meeting link: {e}"
    except MeetingJoinError as e:
        status_db[session_id]["status"] = "failed"
        status_db[session_id]["message"] = f"Could not join room after retries: {e}"
    except Exception as e:
        status_db[session_id]["status"] = "failed"
        status_db[session_id]["message"] = f"System Error: {str(e)}"
    finally:
        if bot:
            try:
                bot.leave()
            except Exception:
                pass


@api_router.post("/join", response_model=JoinMeetingResponse)
async def submit_meeting(request: JoinMeetingRequest, background_tasks: BackgroundTasks):
    """
    Accepts a meeting link and starts the background execution.
    """
    # Create an identifier
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    # Run the bot synchronously in a separate OS thread to avoid locking FastAPI's async event loop
    thread = threading.Thread(target=bot_lifecycle_task, args=(session_id, request.meeting_link))
    thread.start()

    return JoinMeetingResponse(session_id=session_id)


@api_router.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str):
    """
    Poll the current status of the requested meeting task.
    First checks the main database, then falls back to the legacy in-memory db.
    If neither has data yet, return a 'pending' status (pipeline is still booting).
    """
    try:
        from src.models.meeting import Meeting
        # Attempt to find the meeting in the database
        meeting = await Meeting.find_one(Meeting.session_id == session_id)
        if meeting:
            # Map MeetingStatus to Step
            status_val = meeting.status.value if hasattr(meeting.status, 'value') else meeting.status
            status_map = {
                "pending": 0, "processing": 0, "joining": 1, "recording": 2,
                "transcribing": 3, "summarising": 4, "delivering": 5,
                "completed": 6, "failed": 6
            }
            step = status_map.get(status_val, 0)
            return StatusResponse(
                session_id=session_id,
                status=status_val,
                step=step,
                total_steps=6,
                message=f"Pipeline is {status_val}..."
            )
    except Exception as e:
        logger.warning(f"Failed to fetch status from DB for {session_id}: {e}")

    # Fallback to legacy in-memory status
    record = status_db.get(session_id)
    if record:
        return StatusResponse(
            session_id=session_id,
            status=record["status"],
            step=record["step"],
            total_steps=record["total_steps"],
            message=record["message"]
        )

    # Neither DB nor in-memory has this session yet — the background task
    # hasn't inserted the Meeting document.  Return a "pending" status so
    # the frontend keeps polling instead of showing an error.
    return StatusResponse(
        session_id=session_id,
        status="pending",
        step=0,
        total_steps=6,
        message="Pipeline is starting up..."
    )


# Connect /meetings history and details to the database
@api_router.get("/meetings")
async def mock_history():
    try:
        from src.models.meeting import Meeting
        meetings = await Meeting.find_all().to_list()
        # Return a list of dicts that can be JSON serialized, including the PydanticObjectId as str
        return [
            {**m.dict(exclude={"id"}), "id": str(m.id)} for m in meetings
        ]
    except Exception as e:
        logger.error(f"Error fetching meetings: {e}")
        return []

@api_router.get("/meetings/{id}")
async def mock_detail(id: str):
    try:
        from src.models.meeting import Meeting
        from beanie import PydanticObjectId
        meeting = await Meeting.get(PydanticObjectId(id))
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return {**meeting.dict(exclude={"id"}), "id": str(meeting.id)}
    except Exception as e:
        logger.error(f"Error fetching meeting details: {e}")
        raise HTTPException(status_code=404, detail="Meeting not found")

@api_router.get("/settings")
async def mock_settings_get():
    return {
        "storage_backend": "database",
        "stt_provider": "whisper",
        "email_sender": "ai-assistant@company.com"
    }

@api_router.post("/settings")
async def mock_settings_post(data: dict):
    return data
