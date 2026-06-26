import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import Any

import aiosmtplib

logger = logging.getLogger(__name__)


def build_invitation_html(title: str | None, link: str | None) -> str:
    """Build an HTML invitation body containing meeting title and link."""
    safe_title = escape(title or "Upcoming Meeting")
    safe_link = escape(link or "")
    return f"""
    <h2>Meeting Invitation</h2>
    <p><strong>Title:</strong> {safe_title}</p>
    <p><strong>Link:</strong> <a href="{safe_link}">{safe_link}</a></p>
    """


async def send_meeting_invitation(
    meeting: Any,
    participant_emails: list[str],
    settings: Any,
) -> None:
    """Send invitation emails, logging individual failures without aborting."""
    for email in participant_emails:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = (
                f"Meeting Invitation: {meeting.title or 'Upcoming Meeting'}"
            )
            msg["From"] = settings.MAIL_USERNAME
            msg["To"] = email
            html = build_invitation_html(
                title=meeting.title,
                link=meeting.meeting_link,
            )
            msg.attach(MIMEText(html, "html"))
            await aiosmtplib.send(
                msg,
                hostname=settings.MAIL_SERVER,
                port=settings.MAIL_PORT,
                username=settings.MAIL_USERNAME,
                password=settings.MAIL_PASSWORD,
                start_tls=settings.MAIL_STARTTLS,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Invitation to %s failed: %s", email, exc)
