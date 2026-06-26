"""Zoom Meeting SDK page strategy."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.meeting_access import MeetingAccess

logger = logging.getLogger(__name__)


class ZoomSdkStrategy:
    def __init__(self, access: "MeetingAccess") -> None:
        self.access = access

    def join(self, link: str) -> None:
        logger.info("[Zoom SDK] Loading background page: %s", link)
        self.access.driver.get(link)
        logger.info("[Zoom SDK] Background page loaded. The SDK will handle the rest.")

