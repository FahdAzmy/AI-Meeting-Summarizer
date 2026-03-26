import time
import asyncio
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import threading
from datetime import datetime
import uuid

from src.models.requests import JoinMeetingRequest, JoinMeetingResponse, StatusResponse
from modules.meeting_access import MeetingAccess
from modules.errors import MeetingJoinError, PlatformNotSupported, BrowserInitError

api_router = APIRouter()

# In-memory "database" for statuses until the main Pipeline DB is connected 
status_db: Dict[str, Dict[str, Any]] = {}

def bot_lifecycle_task(session_id: str, link: str):
    """
    Background worker that controls the Selenium Bot for this session.
    It updates the global status dictionary.
    """
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
    """
    record = status_db.get(session_id)
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return StatusResponse(
        session_id=session_id,
        status=record["status"],
        step=record["step"],
        total_steps=record["total_steps"],
        message=record["message"]
    )


# Minimal mock endpoints for /meetings history and /settings just to satisfy frontend while incomplete
@api_router.get("/meetings")
async def mock_history():
    return []

@api_router.get("/meetings/{id}")
async def mock_detail(id: str):
    raise HTTPException(status_code=404, detail="Detail parsing not implemented yet")

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
