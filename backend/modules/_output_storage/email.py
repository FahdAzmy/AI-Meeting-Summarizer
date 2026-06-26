"""SMTP delivery for output-storage summary emails."""

from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib
from aiosmtplib import SMTPConnectError, SMTPException

from modules.storage_errors import EmailDeliveryError
from modules._output_storage.constants import (
    EMAIL_CHARSET,
    EMAIL_HTML_SUBTYPE,
    EMAIL_SUBJECT,
)
from modules._output_storage.types import EmailSendResult

logger = logging.getLogger(__name__)


async def dispatch_summary_email(
    *,
    recipients: list[str],
    html_body: str,
    sender: str,
    password: str,
    smtp_host: str,
    smtp_port: int,
) -> EmailSendResult:
    """Send one HTML summary email per recipient using the current behavior."""
    sent: list[str] = []
    failed: list[str] = []

    if not recipients:
        return {"sent": sent, "failed": failed}

    for recipient in recipients:
        msg = build_message(sender=sender, recipient=recipient, html_body=html_body)

        try:
            await aiosmtplib.send(
                msg,
                hostname=smtp_host,
                port=smtp_port,
                username=sender,
                password=password,
                start_tls=True,
                recipients=[recipient],
            )
            sent.append(recipient)
            logger.info("[OS] Email delivered to %r.", recipient)

        except SMTPConnectError as exc:
            logger.error("[OS] Global SMTP connection failure: %s", exc)
            raise EmailDeliveryError(recipient="global", cause=exc) from exc

        except SMTPException as exc:
            logger.warning("[OS] Email bounce for %r: %s", recipient, exc)
            failed.append(recipient)

    logger.info(
        "[OS] Email dispatch complete. sent=%d failed=%d",
        len(sent),
        len(failed),
    )
    return {"sent": sent, "failed": failed}


def build_message(*, sender: str, recipient: str, html_body: str) -> MIMEMultipart:
    """Build the existing multipart/alternative HTML email message."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, EMAIL_HTML_SUBTYPE, EMAIL_CHARSET))
    return msg
