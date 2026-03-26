"""
Meeting Access Module – MeetingAccess
Automates joining/leaving Google Meet, Zoom, and MS Teams using Selenium WebDriver.
Selectors are loaded from config/selectors.json to allow hot-swapping without redeploy.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from modules.errors import (
    BrowserInitError,
    MeetingJoinError,
    PlatformNotSupported,
    WaitingRoomTimeout,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Platform detection patterns
# ──────────────────────────────────────────────────────────────
_PLATFORM_PATTERNS: dict[str, re.Pattern] = {
    "google_meet": re.compile(r"https?://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}", re.IGNORECASE),
    "zoom": re.compile(r"https?://(?:[a-z0-9-]+\.)?zoom\.us/j/\d+", re.IGNORECASE),
    "teams": re.compile(
        r"https?://teams\.microsoft\.com/l/meetup-join/[^\s]+",
        re.IGNORECASE,
    ),
}

_SELECTORS_PATH = Path(__file__).parent.parent / "config" / "selectors.json"


class MeetingAccess:
    """Autonomous Selenium bot that joins, monitors, and leaves virtual meetings."""

    def __init__(
        self,
        *,
        selectors_path: Path | str = _SELECTORS_PATH,
        retry_limit: int = 3,
        headless: bool = False,
    ) -> None:
        self.retry_limit = retry_limit
        self.current_attempt = 0
        self.detected_platform: str = ""

        # Load selector configuration
        try:
            self.selectors: dict = json.loads(Path(selectors_path).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.warning("selectors.json not found or invalid – using empty selectors. %s", exc)
            self.selectors = {}

        # Bootstrap Chrome driver
        try:
            options = self._build_chrome_options(headless=headless)
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome WebDriver initialised successfully.")
        except Exception as exc:  # noqa: BLE001
            raise BrowserInitError(cause=exc) from exc

    # ──────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────

    def join(self, link: str) -> None:
        """Route to the correct platform join logic based on URL detection."""
        self.detected_platform = self._detect_platform(link)
        logger.info("Detected platform: %s. Starting join flow.", self.detected_platform)

        router = {
            "google_meet": self._join_google_meet,
            "zoom": self._join_zoom,
            "teams": self._join_teams,
        }
        router[self.detected_platform](link)

    def wait_until_end(self, *, poll_interval: int = 30, waiting_room_timeout: int = 300) -> None:
        """Block until the meeting ends by polling the DOM every *poll_interval* seconds."""
        logger.info("Waiting for meeting to end (platform=%s).", self.detected_platform)
        platform_sel = self.selectors.get(self.detected_platform, {})
        end_xpath = platform_sel.get("end_text", "")

        while True:
            if self._meeting_has_ended(end_xpath):
                logger.info("Meeting end detected. Exiting wait loop.")
                return
            time.sleep(poll_interval)

    def leave(self) -> None:
        """Terminate the browser and release all resources."""
        logger.info("Leaving meeting and closing browser.")
        try:
            self.driver.quit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error during driver.quit(): %s", exc)

    # ──────────────────────────────────────────────────────────
    # Platform detection
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _detect_platform(url: str) -> str:
        """Return the platform key for *url* or raise PlatformNotSupported."""
        for platform, pattern in _PLATFORM_PATTERNS.items():
            if pattern.match(url):
                return platform
        raise PlatformNotSupported(url)

    # ──────────────────────────────────────────────────────────
    # Chrome setup
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _build_chrome_options(*, headless: bool = False) -> Options:
        options = Options()
        # Fake hardware streams – bypass mic/cam permission dialogs
        options.add_argument("--use-fake-ui-for-media-stream")
        options.add_argument("--use-fake-device-for-media-stream")
        # Reduce bot-detection risk
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        # Performance / stability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        if headless:
            options.add_argument("--headless=new")
        return options

    # ──────────────────────────────────────────────────────────
    # Google Meet join logic (US1 – T015)
    # ──────────────────────────────────────────────────────────

    def _join_google_meet(self, link: str) -> None:
        sel = self.selectors.get("google_meet", {})
        for attempt in range(1, self.retry_limit + 1):
            self.current_attempt = attempt
            try:
                logger.info("[Google Meet] Attempt %d/%d – navigating to %s", attempt, self.retry_limit, link)
                self.driver.get(link)

                wait = WebDriverWait(self.driver, 15)

                # Dismiss pre-join dialog if present
                self._safe_click(wait, sel.get("dismiss_dialog", ""), By.CSS_SELECTOR)

                # Mute mic and camera before joining
                self._safe_click(wait, sel.get("mute_mic", ""), By.CSS_SELECTOR)
                self._safe_click(wait, sel.get("mute_cam", ""), By.CSS_SELECTOR)

                # Click "Join now"
                join_btn = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel.get("join_now_button", "[jsname='V67aGc']")))
                )
                join_btn.click()
                logger.info("[Google Meet] Joined successfully on attempt %d.", attempt)
                return

            except (TimeoutException, NoSuchElementException) as exc:
                logger.warning("[Google Meet] Attempt %d failed: %s", attempt, exc)
                if attempt < self.retry_limit:
                    time.sleep(10)

        raise MeetingJoinError(platform="google_meet", attempt=self.retry_limit)

    # ──────────────────────────────────────────────────────────
    # Zoom join logic (US1 – T016)
    # ──────────────────────────────────────────────────────────

    def _join_zoom(self, link: str) -> None:
        sel = self.selectors.get("zoom", {})
        for attempt in range(1, self.retry_limit + 1):
            self.current_attempt = attempt
            try:
                logger.info("[Zoom] Attempt %d/%d – navigating to %s", attempt, self.retry_limit, link)
                self.driver.get(link)

                wait = WebDriverWait(self.driver, 15)

                # Enter display name
                name_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel.get("name_field", "#inputname"))))
                name_field.clear()
                name_field.send_keys("AI Meeting Assistant")

                # Click Join
                join_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel.get("join_button", ".preview-join-button"))))
                join_btn.click()

                # Detect and handle waiting room
                self._handle_zoom_waiting_room(wait, sel)

                logger.info("[Zoom] Joined successfully on attempt %d.", attempt)
                return

            except WaitingRoomTimeout:
                raise
            except (TimeoutException, NoSuchElementException) as exc:
                logger.warning("[Zoom] Attempt %d failed: %s", attempt, exc)
                if attempt < self.retry_limit:
                    time.sleep(10)

        raise MeetingJoinError(platform="zoom", attempt=self.retry_limit)

    def _handle_zoom_waiting_room(self, wait: WebDriverWait, sel: dict) -> None:
        """Poll for waiting room indicator and raise WaitingRoomTimeout if exceeded."""
        deadline = time.time() + 300  # 300-second hard limit (MA-004)
        wr_xpath = sel.get("waiting_room_text", "//p[contains(text(), 'Please wait')]")
        while time.time() < deadline:
            try:
                self.driver.find_element(By.XPATH, wr_xpath)
                logger.debug("[Zoom] Still in waiting room…")
                time.sleep(10)
            except NoSuchElementException:
                return  # No longer in waiting room
        raise WaitingRoomTimeout(timeout_seconds=300)

    # ──────────────────────────────────────────────────────────
    # MS Teams join logic (US1 – T017)
    # ──────────────────────────────────────────────────────────

    def _join_teams(self, link: str) -> None:
        sel = self.selectors.get("teams", {})
        for attempt in range(1, self.retry_limit + 1):
            self.current_attempt = attempt
            try:
                logger.info("[Teams] Attempt %d/%d – navigating to %s", attempt, self.retry_limit, link)
                self.driver.get(link)

                wait = WebDriverWait(self.driver, 15)

                # Bypass "Open app" prompt – choose "Continue on this browser"
                use_browser = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel.get("use_browser_link", "a[data-tid='joinOnWeb']")))
                )
                use_browser.click()

                # Continue without audio/video if prompted
                self._safe_click(wait, sel.get("continue_without_audio", "[data-tid='prejoin-ok-cta']"), By.CSS_SELECTOR)

                # Mute mic
                self._safe_click(wait, sel.get("mute_mic", "[data-tid='toggle-mute']"), By.CSS_SELECTOR)

                # Join call
                join_btn = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel.get("join_button", "[data-tid='call-join-button']")))
                )
                join_btn.click()
                logger.info("[Teams] Joined successfully on attempt %d.", attempt)
                return

            except (TimeoutException, NoSuchElementException) as exc:
                logger.warning("[Teams] Attempt %d failed: %s", attempt, exc)
                if attempt < self.retry_limit:
                    time.sleep(10)

        raise MeetingJoinError(platform="teams", attempt=self.retry_limit)

    # ──────────────────────────────────────────────────────────
    # End-detection helpers (US2 – T021, T022)
    # ──────────────────────────────────────────────────────────

    def _meeting_has_ended(self, end_xpath: str) -> bool:
        """Return True if an end-screen element is found in the DOM."""
        # Google Meet: data-call-ended attribute (T021)
        if self.detected_platform == "google_meet":
            try:
                self.driver.find_element(By.CSS_SELECTOR, "[data-call-ended='true']")
                return True
            except NoSuchElementException:
                pass

        # Zoom: URL change or disconnect dialog (T022)
        if self.detected_platform == "zoom":
            current_url = self.driver.current_url
            if "meeting/end" in current_url or "reason=ended" in current_url:
                return True
            try:
                dialog = self.driver.find_element(By.CSS_SELECTOR, ".zm-modal-body-title")
                if "ended" in dialog.text.lower():
                    return True
            except NoSuchElementException:
                pass

        # Generic xpath check (all platforms)
        if end_xpath:
            try:
                self.driver.find_element(By.XPATH, end_xpath)
                return True
            except NoSuchElementException:
                pass

        return False

    # ──────────────────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────────────────

    def _safe_click(self, wait: WebDriverWait, selector: str, by: str = By.CSS_SELECTOR) -> None:
        """Click an element if it is present; silently skip if absent."""
        if not selector:
            return
        try:
            el = wait.until(EC.element_to_be_clickable((by, selector)))
            el.click()
        except (TimeoutException, NoSuchElementException):
            pass
