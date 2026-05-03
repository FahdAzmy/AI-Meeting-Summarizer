"""
src/helpers/zoom_sdk.py
-----------------------
Zoom Meeting SDK helper utilities.

This module centralises all Zoom-SDK-related logic so that the rest of
the codebase (routes, orchestrator, tests) can remain free of SDK details.

Responsibilities
----------------
1. **URL parsing** — extract the numeric meeting ID and optional passcode
   from any valid Zoom meeting URL.
2. **JWT generation** — create a short-lived HS256 signature token that
   the frontend Zoom Meeting SDK uses to authenticate its ``ZoomMtg.join()``
   call.  The ``ZOOM_SDK_CLIENT_SECRET`` is **never** exposed to the browser.

Usage
-----
    from src.helpers.zoom_sdk import parse_zoom_url, generate_zoom_signature

    details = parse_zoom_url("https://zoom.us/j/1234567890?pwd=abc")
    # details == {"meeting_number": "1234567890", "passcode": "abc"}

    token = generate_zoom_signature("1234567890", role=0)
    # token == "<JWT string>"
"""

from __future__ import annotations

import logging
import re
import time
from typing import TypedDict

import jwt  # PyJWT >= 2.8.0

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Typed return shapes
# ---------------------------------------------------------------------------


class ZoomMeetingDetails(TypedDict):
    """Parsed fields extracted from a Zoom meeting URL."""

    meeting_number: str
    passcode: str  # empty string when no passcode is present


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Matches both personal and company-vanity Zoom URLs, e.g.:
#   https://zoom.us/j/1234567890
#   https://zoom.us/j/1234567890?pwd=AbCdEf123
#   https://acme.zoom.us/j/9876543210?pwd=xyz
_ZOOM_URL_REGEX = re.compile(
    r"https?://(?:[a-z0-9-]+\.)?zoom\.us/j/(\d+)(?:\?pwd=([a-zA-Z0-9]+))?"
)

# JWT token lifetime in seconds (2 hours, per Zoom documentation)
_TOKEN_LIFETIME_SECONDS = 7200


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def parse_zoom_url(url: str) -> ZoomMeetingDetails | None:
    """Extract meeting ID and passcode from a Zoom meeting URL.

    Parameters
    ----------
    url:
        A Zoom meeting URL.  Both ``zoom.us`` and custom-domain variants
        are supported.

    Returns
    -------
    ZoomMeetingDetails
        A dict with ``meeting_number`` (str) and ``passcode`` (str, may
        be empty).
    None
        If the URL does not match any recognised Zoom pattern.

    Examples
    --------
    >>> parse_zoom_url("https://zoom.us/j/1234567890?pwd=abc123")
    {'meeting_number': '1234567890', 'passcode': 'abc123'}

    >>> parse_zoom_url("https://acme.zoom.us/j/9876543210")
    {'meeting_number': '9876543210', 'passcode': ''}

    >>> parse_zoom_url("https://meet.google.com/abc-defg-hij")
    None
    """
    match = _ZOOM_URL_REGEX.search(url)
    if not match:
        logger.debug("parse_zoom_url: no Zoom pattern found in URL '%s'", url)
        return None

    meeting_number, passcode = match.group(1), match.group(2) or ""
    logger.debug(
        "parse_zoom_url: extracted meeting_number=%s passcode=%s",
        meeting_number,
        passcode,
    )
    return ZoomMeetingDetails(meeting_number=meeting_number, passcode=passcode)


def generate_zoom_signature(
    meeting_number: str,
    role: int,
    sdk_key: str,
    sdk_secret: str,
) -> str:
    """Generate a short-lived Zoom Meeting SDK JWT signature.

    The token is signed with ``HS256`` using ``sdk_secret`` and has a
    2-hour lifetime.  It must **never** be cached or re-used across
    different ``meeting_number`` values.

    Parameters
    ----------
    meeting_number:
        The numeric Zoom meeting identifier (as a string).
    role:
        ``0`` for attendee, ``1`` for host.
    sdk_key:
        The ``ZOOM_SDK_CLIENT_ID`` value (public, safe to include in JWT).
    sdk_secret:
        The ``ZOOM_SDK_CLIENT_SECRET`` value (private, used only for signing).

    Returns
    -------
    str
        A compact JWT token string.

    Raises
    ------
    ValueError
        If ``sdk_key`` or ``sdk_secret`` is empty.
    """
    if not sdk_key or not sdk_secret:
        raise ValueError(
            "ZOOM_SDK_CLIENT_ID and ZOOM_SDK_CLIENT_SECRET must both be set "
            "to generate a Zoom SDK signature."
        )

    now = int(time.time())
    payload = {
        "sdkKey": sdk_key,
        "appKey": sdk_key,        # required by some SDK versions
        "mn": meeting_number,
        "role": role,
        "iat": now,
        "exp": now + _TOKEN_LIFETIME_SECONDS,
        "tokenExp": now + _TOKEN_LIFETIME_SECONDS,
    }

    token: str = jwt.encode(payload, sdk_secret, algorithm="HS256")
    logger.debug(
        "generate_zoom_signature: token generated for meeting_number=%s role=%d",
        meeting_number,
        role,
    )
    return token
