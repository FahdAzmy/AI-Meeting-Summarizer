"""Public OutputStorage service implementation."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from config.settings import Config
from modules.storage_errors import InvalidBackendError
from modules._output_storage.constants import VALID_BACKENDS
from modules._output_storage.database import persist_meeting_report
from modules._output_storage.email import dispatch_summary_email
from modules._output_storage.renderer import render_email_body
from modules._output_storage.types import EmailSendResult

if TYPE_CHECKING:
    from src.models.meeting import Meeting

logger = logging.getLogger(__name__)


class OutputStorage:
    """Async facade for meeting-result persistence and email distribution."""

    def __init__(
        self,
        backend: str = "database",
        config: Config | None = None,
    ) -> None:
        cfg = config or Config()

        if backend not in VALID_BACKENDS:
            raise InvalidBackendError(backend)

        self.backend: str = backend

        self.email_sender: str = cfg.EMAIL_SENDER
        self.email_password: str = cfg.EMAIL_PASSWORD
        self.smtp_host: str = cfg.EMAIL_SMTP_HOST
        self.smtp_port: int = cfg.EMAIL_SMTP_PORT

        self.mongo_uri: str = cfg.MONGO_URI
        self.mongo_db: str = cfg.MONGO_DB

        logger.debug(
            "OutputStorage initialised \u2014 backend=%r smtp_host=%r",
            self.backend,
            self.smtp_host,
        )

    async def _store_to_database(
        self,
        meeting: Meeting,
        report: dict[str, Any],
        transcript: dict[str, Any],
    ) -> None:
        """Persist MeetingReport data onto the Beanie Meeting document."""
        await persist_meeting_report(meeting, report, transcript)

    @staticmethod
    async def _format_email_body(report: dict[str, Any]) -> str:
        """Render MeetingReport data as the existing styled HTML email body."""
        return render_email_body(report)

    async def send_email(
        self,
        recipients: list[str],
        report: dict[str, Any],
    ) -> EmailSendResult:
        """Dispatch the HTML summary email to every address in recipients."""
        if not recipients:
            return {"sent": [], "failed": []}

        html_body = await self._format_email_body(report)
        return await dispatch_summary_email(
            recipients=recipients,
            html_body=html_body,
            sender=self.email_sender,
            password=self.email_password,
            smtp_host=self.smtp_host,
            smtp_port=self.smtp_port,
        )

    async def store(
        self,
        meeting: Meeting,
        report: dict[str, Any],
        transcript: dict[str, Any],
    ) -> None:
        """Route incoming analysis results to the configured persistence target."""
        meeting_id: str = str(getattr(meeting, "id", "unknown"))
        t_start: float = time.monotonic()

        logger.info(
            "[OS] store() started \u2014 meeting=%r backend=%r",
            meeting_id,
            self.backend,
        )

        await self._store_to_database(meeting, report, transcript)

        elapsed_ms: float = (time.monotonic() - t_start) * 1000
        logger.info(
            "[OS] store() complete \u2014 meeting=%r backend=%r elapsed_ms=%.1f",
            meeting_id,
            self.backend,
            elapsed_ms,
        )
