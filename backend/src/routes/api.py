"""
src/routes/api.py
-----------------
REST API router for the AI Meeting Summariser backend.

Endpoints
---------
POST /trigger  — Launch the full AI pipeline as a background task (T016/T017).
POST /join     — Legacy endpoint for direct bot lifecycle management.
GET  /status   — Poll in-memory session status (legacy).
GET  /meetings — Meeting history.
"""

import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field
import threading
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.requests import JoinMeetingRequest, JoinMeetingResponse, StatusResponse
from src.helpers.db import get_db

logger = logging.getLogger(__name__)

api_router = APIRouter()


# ---------------------------------------------------------------------------
# T016 / T017 — Pipeline trigger endpoint (Phase 6)
# ---------------------------------------------------------------------------


class TriggerRequest(BaseModel):
    """Request body for the ``POST /trigger`` endpoint."""

    meeting_link: str = Field(
        ...,
        description="URL of the meeting to join.",
        examples=["https://meet.google.com/abc-defg-hij"],
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

    message: str = Field(..., description="Human-readable confirmation message.")
    meeting_link: str = Field(..., description="Echo of the submitted meeting link.")
    storage: str = Field(..., description="Echo of the selected storage backend.")


@api_router.post("/trigger", response_model=TriggerResponse, status_code=202)
async def trigger_pipeline(
    request: TriggerRequest,
    background_tasks: BackgroundTasks,
):
    """Launch the full AI pipeline as a detached background task."""
    from src.orchestrator import run_pipeline

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

status_db: Dict[str, Dict[str, Any]] = {}


def bot_lifecycle_task(session_id: str, link: str):
    """Background worker that controls the Selenium Bot for this session."""
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
        "message": "Initializing browser and joining meeting...",
    }

    bot = None
    try:
        bot = MeetingAccess(headless=True)
        bot.join(link)

        status_db[session_id]["status"] = "recording"
        status_db[session_id]["step"] = 2
        status_db[session_id]["message"] = (
            f"Connected to {bot.detected_platform}! Active listening mode..."
        )

        time.sleep(15)

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
async def submit_meeting(
    request: JoinMeetingRequest, background_tasks: BackgroundTasks
):
    """Accepts a meeting link and starts the background execution."""
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    thread = threading.Thread(
        target=bot_lifecycle_task, args=(session_id, request.meeting_link)
    )
    thread.start()

    return JoinMeetingResponse(session_id=session_id)


@api_router.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str, db: AsyncSession = Depends(get_db)):
    """Poll the current status of the requested meeting task."""
    try:
        from src.models.meeting import Meeting

        # Query using SQLAlchemy
        result = await db.execute(select(Meeting).where(Meeting.session_id == session_id))
        meeting = result.scalar_one_or_none()
        if meeting:
            status_val = (
                meeting.status.value
                if hasattr(meeting.status, "value")
                else meeting.status
            )
            status_map = {
                "pending": 0,
                "processing": 0,
                "joining": 1,
                "recording": 2,
                "transcribing": 3,
                "summarising": 4,
                "delivering": 5,
                "completed": 6,
                "failed": 6,
            }
            step = status_map.get(status_val, 0)
            return StatusResponse(
                session_id=session_id,
                status=status_val,
                step=step,
                total_steps=6,
                message=f"Pipeline is {status_val}...",
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
            message=record["message"],
        )

    return StatusResponse(
        session_id=session_id,
        status="pending",
        step=0,
        total_steps=6,
        message="Pipeline is starting up...",
    )


@api_router.get("/meetings")
async def mock_history(db: AsyncSession = Depends(get_db)):
    """Retrieve history of all meetings."""
    try:
        from src.models.meeting import Meeting

        result = await db.execute(select(Meeting))
        meetings = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "title": m.title,
                "meeting_link": m.meeting_link,
                "session_id": m.session_id,
                "platform": m.platform,
                "scheduled_time": m.scheduled_time.isoformat() if m.scheduled_time else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "date": m.created_at.isoformat() if m.created_at else None,
                "status": m.status.value if hasattr(m.status, "value") else m.status,
                "error_message": m.error_message,
                "duration_minutes": m.duration_minutes,
                "transcript": m.transcript,
                "summary": m.summary,
                "action_items": m.action_items,
                "decisions": m.decisions,
                "follow_up": m.follow_up,
                "speaker_stats": m.speaker_stats,
                "company_id": str(m.company_id) if m.company_id else None,
                "created_by": str(m.created_by) if m.created_by else None,
            }
            for m in meetings
        ]
    except Exception as e:
        logger.error(f"Error fetching meetings: {e}")
        return []


@api_router.get("/meetings/{id}")
async def mock_detail(id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve details of a specific meeting."""
    try:
        from src.models.meeting import Meeting

        try:
            meeting_uuid = uuid.UUID(id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        result = await db.execute(select(Meeting).where(Meeting.id == meeting_uuid))
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        return {
            "id": str(meeting.id),
            "title": meeting.title,
            "meeting_link": meeting.meeting_link,
            "session_id": meeting.session_id,
            "platform": meeting.platform,
            "scheduled_time": meeting.scheduled_time.isoformat() if meeting.scheduled_time else None,
            "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
            "date": meeting.created_at.isoformat() if meeting.created_at else None,
            "status": meeting.status.value if hasattr(meeting.status, "value") else meeting.status,
            "error_message": meeting.error_message,
            "duration_minutes": meeting.duration_minutes,
            "transcript": meeting.transcript,
            "summary": meeting.summary,
            "action_items": meeting.action_items,
            "decisions": meeting.decisions,
            "follow_up": meeting.follow_up,
            "speaker_stats": meeting.speaker_stats,
            "company_id": str(meeting.company_id) if meeting.company_id else None,
            "created_by": str(meeting.created_by) if meeting.created_by else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching meeting details: {e}")
        raise HTTPException(status_code=404, detail="Meeting not found")


@api_router.get("/settings")
async def mock_settings_get():
    return {
        "storage_backend": "database",
        "stt_provider": "whisper",
        "email_sender": "ai-assistant@company.com",
    }


@api_router.post("/settings")
async def mock_settings_post(data: dict):
    return data
