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

All database status mutations are committed immediately so the frontend
dashboard reflects progress in real-time (<150 ms target).

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
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dependency resolution — real packages with lightweight sentinel fallback
# ---------------------------------------------------------------------------
# Each block tries the real import first.  If the package is not installed
# (e.g. in a minimal test environment) it installs a sentinel class whose
# constructor raises RuntimeError.  Tests patch these names *before* calling
# run_pipeline so the sentinel is never reached in correctly-written tests.

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


# ---------------------------------------------------------------------------
# Audio extraction helper
# ---------------------------------------------------------------------------


def _extract_audio(video_path: str) -> str:
    """Extract audio track from an OBS video recording using ffmpeg.

    OBS only records video containers (MP4/MKV/MOV), so even a 30-second
    meeting produces a ~28 MB file.  Extracting just the audio yields a
    ~500 KB WAV, which uploads much faster to the STT API.

    Parameters
    ----------
    video_path:
        Path to the OBS video recording (e.g. ``.mp4``).

    Returns
    -------
    str
        Path to the extracted ``.wav`` file (same directory, ``.wav`` suffix).
        If ffmpeg is unavailable, returns the original video path unchanged
        (Deepgram can handle MP4 natively, just slower to upload).
    """
    audio_path = str(Path(video_path).with_suffix(".wav"))

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",          # overwrite without asking
                "-i", video_path,         # input video
                "-vn",                    # drop video stream
                "-acodec", "pcm_s16le",   # 16-bit PCM WAV
                "-ar", "16000",           # 16 kHz sample rate (optimal for STT)
                "-ac", "1",               # mono
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_pipeline(
    meeting_link: str,
    emails: list[str],
    storage: str,
    session_id: str | None = None,
) -> None:
    """Orchestrate the full AI meeting-summariser pipeline.

    Parameters
    ----------
    meeting_link:
        URL of the meeting room to join (Zoom, Google Meet, Teams, …).
    emails:
        List of recipient e-mail addresses for the final report.
    storage:
        Storage backend identifier (``"email"``, ``"sheets"``, ``"db"``).
        Passed unchanged to :class:`OutputStorage`.

    Notes
    -----
    * Blocking I/O calls (``join`` / ``start``) are offloaded to a thread
      pool via :func:`asyncio.to_thread` to prevent stalling the event loop.
    * Any unhandled exception causes the meeting document to be marked
      ``FAILED`` and is logged at ERROR level — it is *not* re-raised so
      the FastAPI worker stays healthy.
    """
    # ── Create & persist initial meeting record ─────────────────────────────
    meeting: Any = Meeting(meeting_link=meeting_link, session_id=session_id)
    await meeting.insert()

    logger.info("Pipeline started | link=%s | storage=%s", meeting_link, storage)

    try:
        # ── Stage 1: Join meeting ───────────────────────────────────────────
        meeting.status = MeetingStatus.JOINING
        await meeting.save()
        logger.debug("Stage JOINING | id=%s", meeting.id)

        access = MeetingAccess()
        await asyncio.to_thread(access.join, meeting_link)

        # ── Stage 2: Record audio ───────────────────────────────────────────
        meeting.status = MeetingStatus.RECORDING
        await meeting.save()
        logger.debug("Stage RECORDING | id=%s", meeting.id)

        capture = AudioCapture()
        await asyncio.to_thread(capture.start)

        # Wait for the meeting to end, then stop recording
        await asyncio.to_thread(access.wait_until_end)
        raw_recording: str = await asyncio.to_thread(capture.stop)

        # Leave the meeting room and release browser resources
        await asyncio.to_thread(access.leave)

        # Extract audio from the OBS video container (MP4 → WAV)
        # This reduces file size from ~28 MB to ~500 KB.
        audio_path: str = await asyncio.to_thread(_extract_audio, raw_recording)

        # ── Stage 3: Transcribe ─────────────────────────────────────────────
        meeting.status = MeetingStatus.TRANSCRIBING
        await meeting.save()
        logger.debug("Stage TRANSCRIBING | id=%s", meeting.id)

        transcriber = Transcription(provider="deepgram")
        # transcribe() is synchronous (blocking network I/O) — run in thread
        transcript: dict[str, Any] = await asyncio.to_thread(
            transcriber.transcribe, audio_path
        )

        # ── Stage 4: Summarise ──────────────────────────────────────────────
        meeting.status = MeetingStatus.SUMMARISING
        await meeting.save()
        logger.debug("Stage SUMMARISING | id=%s", meeting.id)

        summariser = Summarisation()
        # generate_report() is synchronous (blocking LLM API) — run in thread
        report: dict[str, Any] = await asyncio.to_thread(
            summariser.generate_report, transcript
        )

        # ── Stage 5: Deliver / store ────────────────────────────────────────
        meeting.status = MeetingStatus.DELIVERING
        await meeting.save()
        logger.debug("Stage DELIVERING | id=%s", meeting.id)

        # Map the frontend storage value to OutputStorage backend
        backend_map = {"email": "database", "sheets": "google_sheets", "db": "database"}
        backend = backend_map.get(storage, "database")

        output = OutputStorage(backend=backend)
        await output.store(meeting, report, transcript)

        # Send email report if recipients were provided
        if emails:
            await output.send_email(recipients=emails, report=report)

        # ── Terminal: success ───────────────────────────────────────────────
        meeting.status = MeetingStatus.COMPLETED
        await meeting.save()
        logger.info("Pipeline COMPLETED | id=%s", meeting.id)

    except Exception:  # noqa: BLE001
        # Mark the meeting as failed so the dashboard can surface the error.
        # Nothing escapes to the FastAPI worker — the server must stay alive.
        logger.exception(
            "Pipeline FAILED | id=%s | link=%s",
            getattr(meeting, "id", "unknown"),
            meeting_link,
        )
        try:
            meeting.status = MeetingStatus.FAILED
            await meeting.save()
        except Exception:  # noqa: BLE001
            logger.exception(
                "Could not persist FAILED status | id=%s",
                getattr(meeting, "id", "unknown"),
            )

