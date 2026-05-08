"""Platform detection and URL rewriting helpers."""

from __future__ import annotations

import logging
import re
import urllib.parse

from modules.errors import PlatformNotSupported

from .types import Platform

logger = logging.getLogger(__name__)

PLATFORM_PATTERNS: dict[Platform, re.Pattern[str]] = {
    Platform.GOOGLE_MEET: re.compile(
        r"https?://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}", re.IGNORECASE
    ),
    Platform.ZOOM: re.compile(
        r"https?://(?:[a-z0-9-]+\.)?zoom\.us/j/\d+", re.IGNORECASE
    ),
    Platform.TEAMS: re.compile(
        r"https?://(?:teams\.microsoft\.com/l/meetup-join/[^\s]+|teams\.live\.com/meet/[^\s]+)",
        re.IGNORECASE,
    ),
    Platform.ZOOM_SDK: re.compile(
        r"https?://localhost:\d+/zoom-meeting.*", re.IGNORECASE
    ),
}


def detect_platform(url: str) -> Platform:
    """Return the platform key for *url* or raise PlatformNotSupported."""
    for platform, pattern in PLATFORM_PATTERNS.items():
        if pattern.match(url):
            return platform
    raise PlatformNotSupported(url)


def teams_web_url(link: str) -> str:
    """Rewrite ``teams.live.com/meet/`` links to the browser deep-link."""
    parsed = urllib.parse.urlparse(link)
    if "teams.live.com" not in parsed.netloc:
        return link

    match = re.match(r"/meet/([^/?#]+)", parsed.path)
    if not match:
        logger.warning("[Teams] Could not parse meeting ID from: %s", link)
        return link

    meeting_id = match.group(1)
    extra = "anon=true&launchType=web"
    full_qs = f"{parsed.query}&{extra}" if parsed.query else extra
    web_url = f"https://teams.live.com/v2/#/meet/{meeting_id}?{full_qs}"
    logger.info("[Teams] Rewrote URL to web deep-link: %s", web_url)
    return web_url


def zoom_web_client_url(link: str) -> str:
    """Rewrite a standard Zoom meeting URL to the web-client join URL."""
    parsed = urllib.parse.urlparse(link)
    match = re.match(r"/j/(\d+)", parsed.path)
    if not match:
        return link

    meeting_id = match.group(1)
    web_url = urllib.parse.urlunparse(
        (parsed.scheme, parsed.netloc, f"/wc/{meeting_id}/join", "", parsed.query, "")
    )
    logger.info("[Zoom] Rewrote URL to web client: %s", web_url)
    return web_url

