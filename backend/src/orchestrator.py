"""
src/orchestrator.py
-------------------
Central pipeline orchestrator for the AI Meeting Summariser.

This module is the *only* entry-point that the FastAPI layer touches.
It bridges the REST API to the five internal AI modules and keeps the
FastAPI event-loop unblocked by running blocking calls inside a thread
pool via :func:`asyncio.to_thread`.

Pipeline sequence
-----------------
  JOINING      →  MeetingAccess.join()           (blocking → thread pool)
  RECORDING    →  AudioCapture.start()           (blocking → thread pool)
  TRANSCRIBING →  Transcription.transcribe()     (async)
  SUMMARISING  →  Summarisation.generate_report() (async)
  DELIVERING   →  OutputStorage.store()          (async)
  COMPLETED / FAILED  (terminal states)

All database status mutations use short-lived SQLAlchemy async sessions so
the database connection is never held open during long blocking operations.

Testability design
------------------
Every dependency (``Meeting``, ``MeetingAccess``, …) is imported at the
*module level* via a try/except guard that installs a lightweight sentinel
stub when the real package is absent.  This means:

* ``patch("src.orchestrator.Meeting")`` always has a stable target.
* No real AI library needs to be installed in CI / unit-test environments.
* The sentinel raises ``RuntimeError`` if accidentally called without mocking,
  which makes test misconfiguration immediately obvious.

Usage
-----
    from src.orchestrator import run_pipeline

    # Launched by FastAPI's BackgroundTasks:
    background_tasks.add_task(run_pipeline, meeting_link, emails, storage)
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dependency resolution — real packages with lightweight sentinel fallback
# ---------------------------------------------------------------------------

def _missing(name: str):
    """Return a sentinel class that blows up loudly if ever instantiated."""
    class _Sentinel:
        def __init__(self, *a, **kw):
            raise RuntimeError(
                f"{name} is not installed and was not mocked. "
                "Patch it in your test or install the real package."
            )
    _Sentinel.__name__ = name
    _Sentinel.__qualname__ = name
    return _Sentinel


try:
    from src.models.meeting import Meeting, MeetingStatus
except ImportError:  # pragma: no cover
    Meeting = _missing("Meeting")           # type: ignore[assignment,misc]
    MeetingStatus = _missing("MeetingStatus")  # type: ignore[assignment,misc]

try:
    from modules.meeting_access import MeetingAccess
except ImportError:  # pragma: no cover
    MeetingAccess = _missing("MeetingAccess")  # type: ignore[assignment,misc]

try:
    from modules.audio_capture import AudioCapture
except ImportError:  # pragma: no cover
    AudioCapture = _missing("AudioCapture")  # type: ignore[assignment,misc]

try:
    from modules.transcription import Transcription
except ImportError:  # pragma: no cover
    Transcription = _missing("Transcription")  # type: ignore[assignment,misc]

try:
    from modules.summarisation import Summarisation
except ImportError:  # pragma: no cover
    Summarisation = _missing("Summarisation")  # type: ignore[assignment,misc]

try:
    from modules.output_storage import OutputStorage
except ImportError:  # pragma: no cover
    OutputStorage = _missing("OutputStorage")  # type: ignore[assignment,misc]

try:
    from config.settings import Config as _Config
    from src.helpers.zoom_sdk import parse_zoom_url as _parse_zoom_url
    _zoom_sdk_available = True
except ImportError:  # pragma: no cover
    _Config = _missing("Config")  # type: ignore[assignment,misc]
    _parse_zoom_url = None  # type: ignore[assignment]
    _zoom_sdk_available = False

# Module-level DB imports — must be at top level so tests can patch them
from sqlalchemy import select  # noqa: E402
from src.helpers.db import SessionLocal  # noqa: E402  (after sentinels)
from src.models.company import Company  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_platform(link: str) -> str | None:
    link_lower = link.lower()
    if "zoom.us" in link_lower:
        return "Zoom"
    if "meet.google.com" in link_lower:
        return "Google Meet"
    if "teams.microsoft.com" in link_lower or "teams.live.com" in link_lower:
        return "Microsoft Teams"
    return "Unknown"


def _extract_names_from_emails(emails: list[str]) -> list[str]:
    """Extract likely display names from email addresses."""
    names: list[str] = []
    for email in emails:
        local = email.split("@")[0]
        local = local.replace(".", " ").replace("_", " ").replace("-", " ")
        parts = [p for p in local.split() if not p.isdigit()]
        if parts:
            name = " ".join(p.capitalize() for p in parts)
            names.append(name)
    return names


def _extract_audio(video_path: str) -> str:
    """Extract audio track from an OBS video recording using ffmpeg."""
    audio_path = str(Path(video_path).with_suffix(".wav"))

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                audio_path,
            ],
            check=True,
            capture_output=True,
            timeout=60,
        )
        video_size = os.path.getsize(video_path)
        audio_size = os.path.getsize(audio_path)
        logger.info(
            "Audio extracted: %s (%d KB) → %s (%d KB)",
            video_path, video_size // 1024,
            audio_path, audio_size // 1024,
        )
        return audio_path

    except FileNotFoundError:
        logger.warning(
            "ffmpeg not found on PATH — sending raw video to STT API. "
            "Install ffmpeg to reduce upload size."
        )
        return video_path
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "ffmpeg audio extraction failed (%s) — using raw video.", exc
        )
        return video_path


async def _get_or_create_default_company(db) -> Any:
    """Return the first Company row, creating a default one if none exist."""

    result = await db.execute(select(Company).limit(1))
    company = result.scalar_one_or_none()
    if company is None:
        company = Company(name="Default Company", subscription_plan="free")
        db.add(company)
        await db.commit()
        await db.refresh(company)
        logger.info("Created default company id=%s", company.id)
    return company


async def _update_meeting_status(
    meeting_id: uuid.UUID,
    status: Any,
    error_message: str | None = None,
    **extra_fields: Any,
) -> None:
    """Open a short-lived session to update a meeting's status and optional fields."""

    async with SessionLocal() as db:
        result = await db.execute(
            select(Meeting).where(Meeting.id == meeting_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            logger.warning("_update_meeting_status: meeting %s not found", meeting_id)
            return
        row.status = status
        if error_message is not None:
            row.error_message = error_message
        for field, value in extra_fields.items():
            setattr(row, field, value)
        await db.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_pipeline(
    meeting_link: str,
    emails: list[str],
    storage: str,
    session_id: str | None = None,
) -> None:
    """Orchestrate the full AI meeting-summariser pipeline."""

    # ── Create & persist initial meeting record ──────────────────────────
    platform_name = _detect_platform(meeting_link)
    meeting_id: uuid.UUID | None = None

    try:
        async with SessionLocal() as db:
            company = await _get_or_create_default_company(db)
            new_meeting = Meeting(
                meeting_link=meeting_link,
                session_id=session_id,
                platform=platform_name,
                company_id=company.id,
                status=MeetingStatus.PROCESSING,
            )
            db.add(new_meeting)
            await db.commit()
            await db.refresh(new_meeting)
            meeting_id = new_meeting.id
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Pipeline FAILED to initialise DB record | link=%s | error=%s",
            meeting_link, exc,
        )
        return

    logger.info("Pipeline started | id=%s | link=%s | storage=%s", meeting_id, meeting_link, storage)

    # Keep a lightweight proxy object so the OutputStorage interface (which
    # expects a meeting object with an .id attribute) works without changes.
    class _MeetingProxy:
        def __init__(self, mid: uuid.UUID) -> None:
            self.id = mid

    meeting_proxy = _MeetingProxy(meeting_id)

    try:
        # ── Stage 1: Join meeting ─────────────────────────────────────────
        await _update_meeting_status(meeting_id, MeetingStatus.JOINING)
        logger.debug("Stage JOINING | id=%s", meeting_id)

        # ── Zoom Meeting SDK routing ──────────────────────────────────────
        _use_zoom_sdk = False
        if _zoom_sdk_available and _parse_zoom_url is not None:
            _zoom_details = _parse_zoom_url(meeting_link)
            if _zoom_details:
                _cfg = _Config()
                if _cfg.ZOOM_SDK_CLIENT_ID and _cfg.ZOOM_SDK_CLIENT_SECRET:
                    _use_zoom_sdk = True
                else:
                    logger.warning(
                        "Zoom URL detected but SDK credentials not configured — "
                        "falling back to Selenium for meeting id=%s",
                        meeting_id,
                    )

        if _use_zoom_sdk:
            import urllib.parse as _urlparse
            _sdk_page_url = (
                "http://localhost:3000/zoom-meeting"
                f"?link={_urlparse.quote(meeting_link, safe='')}"
                f"&meeting_id={meeting_id}"
            )
            logger.info("Stage JOINING via Zoom SDK | id=%s | sdk_page=%s", meeting_id, _sdk_page_url)
            access = MeetingAccess()
            await asyncio.to_thread(access.join, _sdk_page_url)
        else:
            logger.info("Stage JOINING via Selenium | id=%s | link=%s", meeting_id, meeting_link)
            access = MeetingAccess()
            await asyncio.to_thread(access.join, meeting_link)

        # ── Stage 2: Start recording ──────────────────────────────────────
        await _update_meeting_status(meeting_id, MeetingStatus.RECORDING)
        logger.debug("Stage RECORDING | id=%s", meeting_id)

        capture = AudioCapture()
        await asyncio.to_thread(capture.start)
        await asyncio.to_thread(access.wait_until_end)

        try:
            raw_recording: str = await asyncio.to_thread(capture.stop)
        except Exception as stop_exc:
            logger.warning("OBS stop failed (%s) — trying to find latest recording.", stop_exc)
            raw_recording = await asyncio.to_thread(capture._find_latest_recording)
            if not raw_recording:
                raise

        await asyncio.to_thread(access.leave)
        audio_path: str = await asyncio.to_thread(_extract_audio, raw_recording)

        # ── Stage 3: Transcribe ───────────────────────────────────────────
        await _update_meeting_status(meeting_id, MeetingStatus.TRANSCRIBING)
        logger.debug("Stage TRANSCRIBING | id=%s", meeting_id)

        _cfg = _Config()
        transcriber = Transcription(provider=_cfg.STT_PROVIDER)
        transcript: dict[str, Any] = await asyncio.to_thread(transcriber.transcribe, audio_path)

        # ── Stage 4: Summarise ────────────────────────────────────────────
        await _update_meeting_status(meeting_id, MeetingStatus.SUMMARISING)
        logger.debug("Stage SUMMARISING | id=%s", meeting_id)

        summariser = Summarisation()
        name_hints = _extract_names_from_emails(emails) if emails else None
        if name_hints:
            logger.info("Participant hints from emails: %s", ", ".join(name_hints))
        report: dict[str, Any] = await asyncio.to_thread(
            summariser.generate_report, transcript, participant_hints=name_hints
        )

        # ── Stage 5: Deliver / store ──────────────────────────────────────
        await _update_meeting_status(meeting_id, MeetingStatus.DELIVERING)
        logger.debug("Stage DELIVERING | id=%s", meeting_id)

        backend_map = {"email": "database", "db": "database"}
        backend = backend_map.get(storage, "database")

        output = OutputStorage(backend=backend)
        # OutputStorage.store() now uses SessionLocal internally via database.py
        await output.store(meeting_proxy, report, transcript)

        if emails:
            await output.send_email(recipients=emails, report=report)

        # ── Terminal: success ─────────────────────────────────────────────
        await _update_meeting_status(meeting_id, MeetingStatus.COMPLETED)
        logger.info("Pipeline COMPLETED | id=%s", meeting_id)

    except Exception as exc:  # noqa: BLE001
        error_msg = "An unexpected error occurred during processing."
        exc_str = str(exc).lower()
        exc_type = type(exc).__name__.lower()

        # Fetch current status for better error message context
        current_status: Any = None
        try:
            async with SessionLocal() as db:
                result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
                row = result.scalar_one_or_none()
                if row:
                    current_status = row.status
        except Exception:
            pass

        if "timeout" in exc_str or "timeout" in exc_type:
            if current_status == MeetingStatus.JOINING:
                error_msg = "We couldn't join the meeting. The link might be invalid, or the host didn't let us in."
            elif current_status == MeetingStatus.TRANSCRIBING:
                error_msg = "The transcription service took too long to respond."
            else:
                error_msg = "A network timeout occurred while processing your meeting."
        elif "stt" in exc_type:
            error_msg = "The transcription service failed to process the audio."
        elif "obs" in exc_str or "websocket" in exc_str:
            error_msg = "There was a problem recording the audio. The recording engine might be offline."
        elif current_status == MeetingStatus.SUMMARISING:
            error_msg = "The AI failed to generate a summary for this meeting."
        elif current_status == MeetingStatus.DELIVERING:
            error_msg = "The summary was created, but we couldn't send the emails."

        logger.exception("Pipeline FAILED | id=%s | link=%s", meeting_id, meeting_link)

        try:
            await _update_meeting_status(
                meeting_id, MeetingStatus.FAILED, error_message=error_msg
            )
        except Exception:  # noqa: BLE001
            logger.exception("Could not persist FAILED status | id=%s", meeting_id)
