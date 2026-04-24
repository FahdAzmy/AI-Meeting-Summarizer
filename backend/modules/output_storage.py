"""
modules/output_storage.py
--------------------------
Output & Storage Module – final stage of the AI Meeting Summarizer pipeline.

Responsibilities
----------------
  1. Persist ``MeetingReport`` + ``TranscriptResult`` data to MongoDB via Beanie.
  2. Dispatch rich-HTML summary emails via aiosmtplib (async SMTP).
  3. Optionally push tabular data to Google Sheets (gspread), with an automatic
     Pandas CSV fallback on any API failure.

All public methods are ``async`` to remain non-blocking within the FastAPI
event loop.  External I/O boundaries (DB, SMTP, Sheets) are isolated behind
thin calls so that they can be cleanly replaced with ``AsyncMock`` in tests.

Error codes
-----------
  OS-001  EmailDeliveryError   – global SMTP failure
  OS-002  SheetsWriteError     – Google Sheets write failure → CSV fallback
  OS-003  DatabaseWriteError   – MongoDB save() failure
  OS-004  InvalidBackendError  – unrecognised backend routing value

Usage
-----
    from modules.output_storage import OutputStorage

    storage = OutputStorage(backend="database")
    await storage.store(meeting, report, transcript)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import aiosmtplib
import gspread
import pandas as pd
from aiosmtplib import SMTPConnectError, SMTPException

from config.settings import Config
from modules.storage_errors import (
    DatabaseWriteError,
    EmailDeliveryError,
    InvalidBackendError,
    SheetsWriteError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HTML template & partial loader
# ---------------------------------------------------------------------------

_TEMPLATES_DIR: Path = Path(__file__).parent / "templates"

# Main email skeleton (page structure, styles, sections headings).
_TEMPLATE_PATH: Path = _TEMPLATES_DIR / "email_meeting_summary.html"

# Partial snippet paths — one file per dynamic fragment.
_PARTIAL_PATHS: dict[str, Path] = {
    "list":             _TEMPLATES_DIR / "partials" / "list.html",
    "action_table":     _TEMPLATES_DIR / "partials" / "action_items_table.html",
    "action_item_row":  _TEMPLATES_DIR / "partials" / "action_item_row.html",
    "follow_up":        _TEMPLATES_DIR / "partials" / "follow_up_section.html",
    "speaker":          _TEMPLATES_DIR / "partials" / "speaker_highlights.html",
    "speaker_row":      _TEMPLATES_DIR / "partials" / "speaker_row.html",
}

# Module-level caches — each file is read from disk only once per process.
_EMAIL_TEMPLATE: str | None = None
_PARTIAL_CACHE: dict[str, str] = {}


def _load_template() -> str:
    """Return the main HTML email template, reading from disk on first call."""
    global _EMAIL_TEMPLATE  # noqa: PLW0603
    if _EMAIL_TEMPLATE is None:
        _EMAIL_TEMPLATE = _TEMPLATE_PATH.read_text(encoding="utf-8")
        logger.debug("[OS] Email template loaded from %s", _TEMPLATE_PATH)
    return _EMAIL_TEMPLATE


def _load_partial(name: str) -> str:
    """Return a cached HTML partial by its *name* key.

    Keys correspond to entries in ``_PARTIAL_PATHS``:
    ``'list'``, ``'action_table'``, ``'follow_up'``, ``'speaker'``.

    Raises
    ------
    KeyError
        If *name* is not a registered partial key.
    """
    if name not in _PARTIAL_CACHE:
        path = _PARTIAL_PATHS[name]  # raises KeyError on unknown name
        _PARTIAL_CACHE[name] = path.read_text(encoding="utf-8")
        logger.debug("[OS] Partial '%s' loaded from %s", name, path)
    return _PARTIAL_CACHE[name]


# Valid routing targets for the store() dispatcher.
_VALID_BACKENDS: frozenset[str] = frozenset({"database", "google_sheets"})


class OutputStorage:
    """Async orchestrator that persists and distributes meeting analysis results.

    Parameters
    ----------
    backend:
        Routing target for the ``store()`` dispatcher.  Must be one of
        ``"database"`` (MongoDB, always executed) or ``"google_sheets"``
        (Sheets push + CSV fallback in addition to DB write).
        Defaults to ``"database"``.
    config:
        Optional pre-built ``Config`` instance.  If omitted a new instance is
        constructed from the environment / .env file.

    Raises
    ------
    InvalidBackendError (OS-004)
        Raised immediately in ``__init__`` if ``backend`` is not one of the
        recognised routing targets.

    Examples
    --------
    >>> storage = OutputStorage(backend="database")
    >>> await storage.store(meeting, report, transcript)
    """

    def __init__(
        self,
        backend: str = "database",
        config: Config | None = None,
    ) -> None:
        cfg = config or Config()

        # Validate backend routing value before any I/O is attempted.
        if backend not in _VALID_BACKENDS:
            raise InvalidBackendError(backend)

        self.backend: str = backend

        # SMTP credentials (injected from Config so tests can pass a stub).
        self.email_sender: str = cfg.EMAIL_SENDER
        self.email_password: str = cfg.EMAIL_PASSWORD
        self.smtp_host: str = cfg.EMAIL_SMTP_HOST
        self.smtp_port: int = cfg.EMAIL_SMTP_PORT

        # MongoDB connection string (used when initialising Beanie externally).
        self.mongo_uri: str = cfg.MONGO_URI
        self.mongo_db: str = cfg.MONGO_DB

        # Google Sheets integration.
        self.sheets_id: str = cfg.GOOGLE_SHEETS_ID
        self.credentials_path: str = cfg.GOOGLE_CREDENTIALS_PATH

        logger.debug(
            "OutputStorage initialised — backend=%r smtp_host=%r",
            self.backend,
            self.smtp_host,
        )

    # ------------------------------------------------------------------
    # Internal helpers – stubs for Phase 3-5 implementation
    # ------------------------------------------------------------------

    async def _store_to_database(
        self,
        meeting: Any,
        report: dict[str, Any],
        transcript: dict[str, Any],
    ) -> None:
        """Persist ``MeetingReport`` data onto the Beanie ``Meeting`` document.

        Maps every analytical field from *report* and *transcript* onto the
        in-memory *meeting* object, then persists it via ``await meeting.save()``.

        Parameters
        ----------
        meeting:
            A Beanie ``Meeting`` document instance (already fetched or created
            by the caller).  Must expose ``.save()`` as an awaitable.
        report:
            ``MeetingReport`` dict produced by ``Summarisation.generate_report()``.
        transcript:
            ``TranscriptResult`` dict produced by the Transcription module.

        Raises
        ------
        DatabaseWriteError (OS-003)
            Re-raised on any exception from ``meeting.save()``.
        """
        # T008 — Map MeetingReport fields onto the document.
        meeting.summary      = report.get("summary")
        meeting.action_items = report.get("action_items", [])
        meeting.decisions    = report.get("decisions", [])
        meeting.follow_up    = report.get("follow_up", [])
        meeting.transcript   = transcript.get("full_text")
        meeting.speaker_stats = report.get("speaker_stats")  # None if unavailable

        # T009 — Force COMPLETED status and calculate duration.
        from src.models.meeting import MeetingStatus
        meeting.status = MeetingStatus.COMPLETED
        duration_seconds = float(transcript.get("duration_seconds", 0.0))
        meeting.duration_minutes = int(duration_seconds // 60)

        meeting_id = str(getattr(meeting, "id", "unknown"))
        logger.info(
            "[OS] Persisting meeting %r to MongoDB. duration_minutes=%d action_items=%d",
            meeting_id,
            meeting.duration_minutes,
            len(meeting.action_items),
        )

        try:
            await meeting.save()
        except Exception as exc:
            logger.error("[OS] Database write failed for meeting %r: %s", meeting_id, exc)
            raise DatabaseWriteError(meeting_id=meeting_id, cause=exc) from exc

        logger.info("[OS] Meeting %r saved successfully (status=COMPLETED).", meeting_id)

    async def _store_to_sheets(
        self,
        meeting: Any,
        report: dict[str, Any],
    ) -> None:
        """Push a tabular summary row to the configured Google Sheets spreadsheet.

        Appends a single row containing the key meeting metrics using the
        ``gspread`` service-account client.  On any ``gspread`` / network
        failure the method transparently falls back to writing a local Pandas
        CSV file (OS-002 / T017) rather than propagating the exception.

        Row schema (T016)
        -----------------
        Date | Participants | Summary | Decisions | Action Items | Duration (min)

        CSV Fallback (T017)
        -------------------
        Written to ``./exports/meeting_<id>_<timestamp>.csv`` on
        ``SheetsWriteError``.

        Parameters
        ----------
        meeting:
            Beanie ``Meeting`` document with ``id`` and ``duration_minutes``.
        report:
            ``MeetingReport`` dict produced by ``Summarisation.generate_report()``.
        """
        # ── Build the row payload ────────────────────────────────────────
        meeting_id: str = str(getattr(meeting, "id", "unknown"))
        date_str: str = datetime.utcnow().strftime("%Y-%m-%d")
        speakers: list = (
            report.get("speaker_stats", {}).get("speakers", [])
            if report.get("speaker_stats")
            else []
        )
        participants: str = ", ".join(s.get("speaker", "") for s in speakers) or "N/A"
        summary: str = report.get("summary", "")
        decisions: str = " | ".join(report.get("decisions", []))
        action_items_str: str = " | ".join(
            f"{a.get('assignee', '?')}: {a.get('task', '?')}"
            for a in report.get("action_items", [])
        )
        duration_min: int = getattr(meeting, "duration_minutes", 0)

        row: list[Any] = [
            date_str,
            participants,
            summary,
            decisions,
            action_items_str,
            duration_min,
        ]

        # ── Attempt Sheets append ────────────────────────────────────────
        try:
            gc = gspread.service_account(filename=self.credentials_path)
            spreadsheet = gc.open_by_key(self.sheets_id)
            spreadsheet.sheet1.append_row(row)
            logger.info(
                "[OS] Row appended to Sheets for meeting %r (sheet_id=%r).",
                meeting_id,
                self.sheets_id,
            )

        except Exception as exc:
            # T017 — Any gspread / network / API exception activates the local
            # CSV fallback.  SheetsWriteError is a subclass of Exception so it
            # is captured here too; the failure is logged and the CSV path
            # ensures data is never silently lost.
            logger.warning(
                "[OS] Sheets write failed for meeting %r — falling back to CSV. Cause: %s",
                meeting_id,
                exc,
            )
            self._write_csv_fallback(meeting_id, row)


    def _write_csv_fallback(
        self,
        meeting_id: str,
        row: list[Any],
    ) -> None:
        """Write a single-row DataFrame to a local CSV file as a Sheets fallback.

        The file is saved to ``./exports/meeting_<id>_<timestamp>.csv``.
        The directory is created automatically if it does not exist.
        """
        export_dir = Path("exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        csv_path = export_dir / f"meeting_{meeting_id}_{timestamp}.csv"

        df = pd.DataFrame(
            [row],
            columns=[
                "Date",
                "Participants",
                "Summary",
                "Decisions",
                "Action Items",
                "Duration (min)",
            ],
        )
        df.to_csv(csv_path, index=False)
        logger.info("[OS] CSV fallback written to %s", csv_path)


    async def _format_email_body(self, report: dict[str, Any]) -> str:
        """Render ``MeetingReport`` data as a styled HTML email body string.

        All markup lives in the template and partial files under
        ``modules/templates/``.  This function is pure data logic:
        it extracts values from *report*, builds row strings by calling
        ``_load_partial()`` with ``str.format_map()``, and injects the
        finished fragments into the main email skeleton.

        Template
        --------
        ``templates/email_meeting_summary.html``   — page skeleton.

        Partials (``templates/partials/``)
        -----------------------------------
        ``list.html``              — ``<ul>`` used for decisions & follow-up.
        ``action_items_table.html``— assignee / task / deadline table.
        ``follow_up_section.html`` — follow-up heading + list (optional).
        ``speaker_highlights.html``— speaker-stats heading + table (optional).

        Parameters
        ----------
        report:
            ``MeetingReport`` dict produced by ``Summarisation.generate_report()``.

        Returns
        -------
        str
            Fully rendered HTML string, ready for a ``MIMEText('html')`` part.
        """
        summary: str       = report.get("summary", "No summary available.")
        decisions: list    = report.get("decisions", [])
        action_items: list = report.get("action_items", [])
        follow_up: list    = report.get("follow_up", [])
        speaker_stats      = report.get("speaker_stats")  # dict | None
        _EM: str           = "\u2014"  # em-dash fallback

        # ── Decisions ───────────────────────────────────────────────────
        if decisions:
            items_html = "".join(f"<li>{d}</li>" for d in decisions)
            decisions_html: str = _load_partial("list").format_map(
                {"items": items_html}
            )
        else:
            decisions_html = "<p><em>No decisions recorded.</em></p>"

        # ── Action items ───────────────────────────────────────────────
        if action_items:
            rows = "".join(
                _load_partial("action_item_row").format_map({
                    "assignee": item.get("assignee", _EM),
                    "task":     item.get("task",     _EM),
                    "deadline": item.get("deadline", _EM),
                })
                for item in action_items
            )
            action_table: str = _load_partial("action_table").format_map(
                {"rows": rows}
            )
        else:
            action_table = "<p><em>No action items recorded.</em></p>"

        # ── Follow-up ────────────────────────────────────────────────
        if follow_up:
            items_html = "".join(f"<li>{f}</li>" for f in follow_up)
            follow_up_section: str = _load_partial("follow_up").format_map(
                {"items": items_html}
            )
        else:
            follow_up_section = ""

        # ── Speaker highlights ─────────────────────────────────────────
        speaker_html: str = ""
        if speaker_stats:
            speakers: list = speaker_stats.get("speakers", [])
            most_active: str = speaker_stats.get("most_active_speaker", "")
            rows = "".join(
                _load_partial("speaker_row").format_map({
                    "speaker":       s.get("speaker", _EM),
                    "speaking_time": f"{s.get('total_speaking_time_sec', 0):.0f}",
                    "share":         f"{s.get('percentage_of_meeting', 0):.1f}",
                    "turns":         s.get("number_of_turns", 0),
                })
                for s in speakers
            )
            most_active_line = (
                f"<p style='margin-top:8px;color:#6b7280'>"
                f"Most active: <strong>{most_active}</strong></p>"
                if most_active else ""
            )
            speaker_html = _load_partial("speaker").format_map({
                "rows":             rows,
                "most_active_line": most_active_line,
            })

        # ── Inject all fragments into the main template ────────────────────
        return _load_template().format_map({
            "summary":           summary,
            "decisions_html":    decisions_html,
            "action_table":      action_table,
            "follow_up_section": follow_up_section,
            "speaker_html":      speaker_html,
        })


    async def send_email(
        self,
        recipients: list[str],
        report: dict[str, Any],
    ) -> dict[str, Any]:
        """Dispatch the HTML summary email to every address in *recipients*.

        Each recipient is attempted independently via ``aiosmtplib.send()``.
        Per-recipient ``SMTPException`` bounces are captured in the returned
        ``failed`` list without aborting remaining sends.
        A connection-level ``SMTPConnectError`` (TLS handshake / DNS failure)
        is treated as a global failure and re-raised as ``EmailDeliveryError``
        (OS-001) because no recipients can ever be reached.

        Parameters
        ----------
        recipients:
            List of target email addresses.
        report:
            ``MeetingReport`` dict used to render the HTML body.

        Returns
        -------
        dict
            ``{"sent": [<successful addresses>], "failed": [<failed addresses>]}``

        Raises
        ------
        EmailDeliveryError (OS-001)
            On a global SMTP connection failure (``SMTPConnectError``).
        """
        sent: list[str] = []
        failed: list[str] = []

        if not recipients:
            return {"sent": sent, "failed": failed}

        html_body = await self._format_email_body(report)

        for recipient in recipients:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Your Meeting Summary – AI Meeting Summarizer"
            msg["From"] = self.email_sender
            msg["To"] = recipient
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            try:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.email_sender,
                    password=self.email_password,
                    start_tls=True,
                    recipients=[recipient],
                )
                sent.append(recipient)
                logger.info("[OS] Email delivered to %r.", recipient)

            except SMTPConnectError as exc:
                # Global failure — TLS handshake never established.
                logger.error("[OS] Global SMTP connection failure: %s", exc)
                raise EmailDeliveryError(recipient="global", cause=exc) from exc

            except SMTPException as exc:
                # Per-recipient bounce — log, capture, continue.
                logger.warning("[OS] Email bounce for %r: %s", recipient, exc)
                failed.append(recipient)

        logger.info(
            "[OS] Email dispatch complete. sent=%d failed=%d",
            len(sent),
            len(failed),
        )
        return {"sent": sent, "failed": failed}

    # ------------------------------------------------------------------
    # Public orchestration entry-point
    # ------------------------------------------------------------------

    async def store(
        self,
        meeting: Any,
        report: dict[str, Any],
        transcript: dict[str, Any],
    ) -> None:
        """Route incoming analysis results to the configured persistence targets.

        Execution order (T018)
        ----------------------
        1. **Always**: ``_store_to_database()`` — MongoDB is the primary store.
           If this fails the error propagates immediately; Sheets is never called.
        2. **If backend == 'google_sheets'**: ``_store_to_sheets()`` — secondary
           enterprise export.  Failures here activate the CSV fallback internally
           and do NOT abort the overall ``store()`` call.

        Telemetry (T019)
        ----------------
        The total wall-clock time for the combined operation is logged at INFO
        level so that observability tooling can measure pipeline latency.

        Parameters
        ----------
        meeting:
            Beanie ``Meeting`` document to persist.
        report:
            ``MeetingReport`` dict from ``Summarisation.generate_report()``.
        transcript:
            ``TranscriptResult`` dict from the Transcription module.

        Raises
        ------
        DatabaseWriteError (OS-003)
            Propagated from ``_store_to_database()`` on MongoDB failure.
        """
        meeting_id: str = str(getattr(meeting, "id", "unknown"))
        t_start: float = time.monotonic()

        logger.info(
            "[OS] store() started — meeting=%r backend=%r",
            meeting_id,
            self.backend,
        )

        # ── Step 1: MongoDB (always, hard failure) ─────────────────────
        await self._store_to_database(meeting, report, transcript)

        # ── Step 2: Google Sheets (conditional, soft failure via fallback)
        if self.backend == "google_sheets":
            await self._store_to_sheets(meeting, report)

        elapsed_ms: float = (time.monotonic() - t_start) * 1000
        logger.info(
            "[OS] store() complete — meeting=%r backend=%r elapsed_ms=%.1f",
            meeting_id,
            self.backend,
            elapsed_ms,
        )
