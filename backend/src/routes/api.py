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
import logging
from typing import Dict, Any
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel, Field
import threading
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.requests import JoinMeetingRequest, JoinMeetingResponse, StatusResponse
from src.helpers.db import get_db
from src.helpers.security import get_current_user
from src.models.meeting import Meeting
from src.models.meeting_participant import MeetingParticipant
from src.models.member import Member
from src.models.user import User
from src.schemas.meeting import CreateMeetingRequest
from src.services.participant_service import resolve_participants

logger = logging.getLogger(__name__)

api_router = APIRouter()


# ---------------------------------------------------------------------------
# T016 / T017 — Pipeline trigger endpoint (Phase 6)
# ---------------------------------------------------------------------------


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
    request: CreateMeetingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Launch the full AI pipeline as a detached background task."""
    from src.orchestrator import run_pipeline

    emails = await resolve_participants(
        db=db,
        team_ids=request.team_ids,
        member_ids=request.member_ids,
        company_id=current_user.company_id,
    )

    logger.info(
        "POST /trigger | link=%s | participants=%d | storage=%s",
        request.meeting_link,
        len(emails),
        request.storage,
    )

    # Generate a tracking session ID
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    background_tasks.add_task(
        run_pipeline,
        meeting_link=request.meeting_link,
        emails=emails,
        storage=request.storage,
        session_id=session_id,
        title=request.title,
        team_ids=request.team_ids,
        member_ids=request.member_ids,
        company_id=current_user.company_id,
        created_by=current_user.id,
    )

    return TriggerResponse(
        session_id=session_id,
        message="Pipeline launched successfully. Track progress via the dashboard.",
        meeting_link=request.meeting_link,
        storage=request.storage,
    )


@api_router.get("/status/{session_id}", response_model=StatusResponse)
async def get_status(session_id: str, db: AsyncSession = Depends(get_db)):
    """Poll the current status of the requested meeting task."""
    try:
        from src.models.meeting import Meeting

        # Query using SQLAlchemy
        result = await db.execute(
            select(Meeting).where(Meeting.session_id == session_id)
        )
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
            message = f"Pipeline is {status_val}..."
            if status_val == "completed":
                message = "Pipeline completed successfully."
            elif status_val == "failed":
                message = meeting.error_message or "Pipeline failed."
            return StatusResponse(
                session_id=session_id,
                status=status_val,
                step=step,
                total_steps=6,
                message=message,
            )
    except Exception as e:
        logger.warning("Failed to fetch status from DB for %s: %s", session_id, e)

    return StatusResponse(
        session_id=session_id,
        status="pending",
        step=0,
        total_steps=6,
        message="Pipeline is starting up...",
    )


async def _meeting_payload(db: AsyncSession, meeting: Meeting) -> dict:
    result = await db.execute(
        select(Member)
        .join(MeetingParticipant, MeetingParticipant.member_id == Member.id)
        .where(MeetingParticipant.meeting_id == meeting.id)
        .order_by(Member.created_at, Member.name)
    )
    participants = [
        {
            "id": str(member.id),
            "name": member.name,
            "email": member.email,
            "team_id": str(member.team_id),
        }
        for member in result.scalars().all()
    ]
    return {
        "id": str(meeting.id),
        "title": meeting.title,
        "meeting_link": meeting.meeting_link,
        "session_id": meeting.session_id,
        "platform": meeting.platform,
        "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
        "date": meeting.created_at.isoformat() if meeting.created_at else None,
        "status": meeting.status.value
        if hasattr(meeting.status, "value")
        else meeting.status,
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
        "participants": participants,
    }


@api_router.get("/meetings")
async def mock_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve history of all meetings."""
    try:
        result = await db.execute(
            select(Meeting)
            .where(Meeting.company_id == current_user.company_id)
            .order_by(Meeting.created_at.desc())
        )
        meetings = result.scalars().all()
        return [await _meeting_payload(db, meeting) for meeting in meetings]
    except Exception as e:
        logger.error(f"Error fetching meetings: {e}")
        return []


@api_router.get("/meetings/{id}")
async def mock_detail(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a specific meeting."""
    try:
        try:
            meeting_uuid = uuid.UUID(id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid UUID format")

        result = await db.execute(
            select(Meeting).where(
                Meeting.id == meeting_uuid,
                Meeting.company_id == current_user.company_id,
            )
        )
        meeting = result.scalar_one_or_none()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        return await _meeting_payload(db, meeting)
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
