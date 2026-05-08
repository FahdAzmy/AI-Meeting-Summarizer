"""Public MeetingAccess facade.

Automates joining/leaving Google Meet, Zoom, MS Teams, and the local Zoom SDK
page using Selenium WebDriver. The public API is intentionally preserved while
the implementation lives in small internal modules under ``modules._meeting_access``.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from modules._meeting_access.browser import build_chrome_options, create_chrome_driver
from modules._meeting_access.constants import SELECTORS_PATH
from modules._meeting_access.detection import (
    PLATFORM_PATTERNS,
    detect_platform,
    teams_web_url,
    zoom_web_client_url,
)
from modules._meeting_access.interactions import safe_click, try_click_strategies
from modules._meeting_access.monitor import (
    click_leave_button,
    is_alone_in_meeting,
    meeting_has_ended,
    wait_for_teams_lobby,
)
from modules._meeting_access.selectors import load_selectors
from modules._meeting_access.strategies.google_meet import GoogleMeetStrategy
from modules._meeting_access.strategies.teams import TeamsStrategy
from modules._meeting_access.strategies.zoom import ZoomStrategy
from modules._meeting_access.strategies.zoom_sdk import ZoomSdkStrategy
from modules._meeting_access.types import (
    LocatorStrategy,
    Platform,
    PlatformSelectors,
    SelectorsConfig,
)
from modules.errors import BrowserInitError

logger = logging.getLogger(__name__)

__all__ = ["MeetingAccess", "Platform"]

# Backward-compatible module constants for tests/tools that import them.
_PLATFORM_PATTERNS = PLATFORM_PATTERNS
_SELECTORS_PATH = SELECTORS_PATH


class MeetingAccess:
    """Autonomous Selenium bot that joins, monitors, and leaves virtual meetings."""

    BOT_NAME = "AI Summarizer"

    def __init__(
        self,
        *,
        selectors_path: Path | str = _SELECTORS_PATH,
        retry_limit: int = 3,
        headless: bool = False,
    ) -> None:
        self.retry_limit = retry_limit
        self.current_attempt = 0
        self.detected_platform: Platform | str = ""
        self.selectors: SelectorsConfig = load_selectors(selectors_path)

        try:
            self.driver = create_chrome_driver(
                headless=headless,
                webdriver_module=webdriver,
                service_cls=Service,
                manager_cls=ChromeDriverManager,
            )
            logger.info("Chrome WebDriver initialised successfully.")
        except Exception as exc:  # noqa: BLE001
            raise BrowserInitError(cause=exc) from exc

    @property
    def platform_key(self) -> str:
        """Return the current platform as a plain selector/config key."""
        if isinstance(self.detected_platform, Platform):
            return self.detected_platform.value
        return self.detected_platform

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def join(self, link: str) -> None:
        """Route to the correct platform join logic based on URL detection."""
        self.detected_platform = self._detect_platform(link)
        logger.info("Detected platform: %s. Starting join flow.", self.detected_platform)

        router = {
            Platform.GOOGLE_MEET: self._join_google_meet,
            Platform.ZOOM: self._join_zoom,
            Platform.ZOOM_SDK: self._join_zoom_sdk,
            Platform.TEAMS: self._join_teams,
        }
        router[self.detected_platform](link)

    def wait_until_end(
        self,
        *,
        poll_interval: int = 5,
        alone_grace_period: int = 30,
        waiting_room_timeout: int = 300,
    ) -> None:
        """Block until the meeting ends or all other participants leave."""
        logger.info("Waiting for meeting to end (platform=%s).", self.detected_platform)
        platform_sel = self.selectors.get(self.platform_key, {})
        end_xpath = platform_sel.get("end_text", "")

        # Kept for API compatibility: the legacy implementation accepts this
        # parameter but Teams lobby handling still uses its established 300s cap.
        _ = waiting_room_timeout

        if self.platform_key == Platform.TEAMS.value:
            wait_for_teams_lobby(self, lobby_timeout=300)

        alone_since: float | None = None
        poll_count = 0
        meeting_start = self._now()
        min_meeting_duration = 30

        while True:
            poll_count += 1
            elapsed_in_meeting = int(self._now() - meeting_start)
            logger.info(
                "Poll #%d | Checking meeting status (platform=%s) | in-meeting %ds...",
                poll_count,
                self.detected_platform,
                elapsed_in_meeting,
            )

            if self._meeting_has_ended(end_xpath):
                logger.info(
                    "Meeting end detected (end screen) after %ds. Exiting wait loop.",
                    elapsed_in_meeting,
                )
                return

            if elapsed_in_meeting < min_meeting_duration:
                logger.debug(
                    "Warm-up period (%ds/%ds) - skipping alone check.",
                    elapsed_in_meeting,
                    min_meeting_duration,
                )
            else:
                is_alone = self._is_alone_in_meeting(platform_sel)
                logger.info("Poll #%d | is_alone=%s", poll_count, is_alone)

                if is_alone:
                    if alone_since is None:
                        alone_since = self._now()
                        logger.info(
                            "Alone in meeting detected - starting %ds grace period.",
                            alone_grace_period,
                        )
                    elapsed = self._now() - alone_since
                    if elapsed >= alone_grace_period:
                        logger.info(
                            "Alone for %.0fs (grace=%ds). Meeting is over.",
                            elapsed,
                            alone_grace_period,
                        )
                        return
                elif alone_since is not None:
                    logger.info("Participant re-joined - resetting alone timer.")
                    alone_since = None

            self._sleep(poll_interval)

    def leave(self) -> None:
        """Click the leave-call button if possible, then quit the browser."""
        logger.info("Leaving meeting and closing browser.")
        try:
            self._click_leave_button()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not click leave button: %s", exc)

        try:
            self._sleep(2)
            self.driver.quit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error during driver.quit(): %s", exc)

    def close(self) -> None:
        """Release the browser driver without attempting in-meeting UI actions."""
        try:
            self.driver.quit()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Error during driver.close cleanup: %s", exc)

    def __enter__(self) -> "MeetingAccess":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Compatibility wrappers and implementation seams
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_platform(url: str) -> Platform:
        return detect_platform(url)

    @staticmethod
    def _build_chrome_options(*, headless: bool = False) -> Options:
        return build_chrome_options(headless=headless)

    @staticmethod
    def _teams_web_url(link: str) -> str:
        return teams_web_url(link)

    @staticmethod
    def _zoom_web_client_url(link: str) -> str:
        return zoom_web_client_url(link)

    def _join_google_meet(self, link: str) -> None:
        GoogleMeetStrategy(self).join(link)

    def _join_zoom(self, link: str) -> None:
        ZoomStrategy(self).join(link)

    def _handle_zoom_waiting_room(self, wait: WebDriverWait, sel: dict[str, Any]) -> None:
        ZoomStrategy(self).handle_waiting_room(wait, sel)

    def _join_zoom_sdk(self, link: str) -> None:
        ZoomSdkStrategy(self).join(link)

    def _join_teams(self, link: str) -> None:
        TeamsStrategy(self).join(link)

    def _meeting_has_ended(self, end_xpath: str) -> bool:
        return meeting_has_ended(self, end_xpath)

    def _is_alone_in_meeting(self, platform_sel: dict[str, Any]) -> bool:
        return is_alone_in_meeting(self, platform_sel)

    def _click_leave_button(self) -> None:
        click_leave_button(self)

    def _try_click_strategies(
        self,
        strategies: list[LocatorStrategy],
        *,
        timeout: int = 5,
    ) -> bool:
        return try_click_strategies(
            wait_factory=self._wait,
            strategies=strategies,
            timeout=timeout,
            logger=logger,
        )

    def _safe_click(self, wait: WebDriverWait, selector: str, by: str = By.CSS_SELECTOR) -> None:
        safe_click(wait, selector, by, logger=logger)

    def _wait(self, timeout: int) -> WebDriverWait:
        return WebDriverWait(self.driver, timeout)

    def _sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def _now(self) -> float:
        return time.time()
