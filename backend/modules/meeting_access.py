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
    "google_meet": re.compile(
        r"https?://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}", re.IGNORECASE
    ),
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
            self.selectors: dict = json.loads(
                Path(selectors_path).read_text(encoding="utf-8")
            )
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.warning(
                "selectors.json not found or invalid – using empty selectors. %s", exc
            )
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
        logger.info(
            "Detected platform: %s. Starting join flow.", self.detected_platform
        )

        router = {
            "google_meet": self._join_google_meet,
            "zoom": self._join_zoom,
            "teams": self._join_teams,
        }
        router[self.detected_platform](link)

    def wait_until_end(
        self,
        *,
        poll_interval: int = 5,
        alone_grace_period: int = 30,
        waiting_room_timeout: int = 300,
    ) -> None:
        """Block until the meeting ends or all other participants leave.

        Detection strategy (Google Meet):
        1. **Banner text**: "No one else is in this meeting" — transient banner
           that appears for ~5-10 seconds when the last participant leaves.
        2. **Participant count**: The badge in the top-right corner showing the
           number of participants.  If it reads "1" for *alone_grace_period*
           consecutive seconds, the agent concludes it is alone.
        3. **End screen**: ``data-call-ended='true'`` — set when the host
           explicitly ends the meeting for everyone.

        Parameters
        ----------
        poll_interval:
            Seconds between each DOM poll (default 5 — fast enough to catch
            the transient banner).
        alone_grace_period:
            Seconds the agent must be alone before it decides the meeting is
            over (default 30).  Prevents false positives from brief
            disconnections.
        waiting_room_timeout:
            Maximum seconds to wait overall (unused here but kept for API
            compat).
        """
        logger.info("Waiting for meeting to end (platform=%s).", self.detected_platform)
        platform_sel = self.selectors.get(self.detected_platform, {})
        end_xpath = platform_sel.get("end_text", "")

        alone_since: float | None = None  # timestamp when we first detected alone
        poll_count = 0

        while True:
            poll_count += 1
            logger.info(
                "Poll #%d | Checking meeting status (platform=%s)…",
                poll_count,
                self.detected_platform,
            )

            # ── Check 1: Host ended the meeting (instant) ────────────────
            if self._meeting_has_ended(end_xpath):
                logger.info("Meeting end detected (end screen). Exiting wait loop.")
                return

            # ── Check 2: Agent is alone in the meeting ───────────────────
            is_alone = self._is_alone_in_meeting(platform_sel)
            logger.info("Poll #%d | is_alone=%s", poll_count, is_alone)

            if is_alone:
                if alone_since is None:
                    alone_since = time.time()
                    logger.info(
                        "Alone in meeting detected — starting %ds grace period.",
                        alone_grace_period,
                    )
                elapsed = time.time() - alone_since
                if elapsed >= alone_grace_period:
                    logger.info(
                        "Alone for %.0fs (grace=%ds). Meeting is over.",
                        elapsed,
                        alone_grace_period,
                    )
                    return
            else:
                # Someone re-joined — reset the grace timer
                if alone_since is not None:
                    logger.info("Participant re-joined — resetting alone timer.")
                    alone_since = None

            time.sleep(poll_interval)

    def leave(self) -> None:
        """Click the leave-call button (if possible), then quit the browser."""
        logger.info("Leaving meeting and closing browser.")
        try:
            self._click_leave_button()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not click leave button: %s", exc)
        # Always quit the driver to release resources
        try:
            time.sleep(2)  # brief pause after clicking leave
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
                logger.info(
                    "[Google Meet] Attempt %d/%d – navigating to %s",
                    attempt,
                    self.retry_limit,
                    link,
                )
                self.driver.get(link)

                wait = WebDriverWait(self.driver, 20)

                # Dismiss pre-join dialog if present
                self._safe_click(wait, sel.get("dismiss_dialog", ""), By.CSS_SELECTOR)

                # ── Enter bot name (guest / not-signed-in flow) ──────────
                # Google Meet uses custom components; try multiple strategies
                # to find the name input field.
                name_entered = False
                name_strategies = [
                    # Strategy 1: CSS selectors from config
                    (By.CSS_SELECTOR, sel.get("name_field", "")),
                    # Strategy 2: XPath by placeholder text
                    (By.XPATH, "//input[@placeholder='Your name']"),
                    # Strategy 3: XPath by aria-label
                    (By.XPATH, "//input[@aria-label='Your name']"),
                    # Strategy 4: Any visible text input on the page
                    (By.XPATH, "//input[@type='text']"),
                    (By.CSS_SELECTOR, "input[type='text']"),
                ]
                for by, selector in name_strategies:
                    if not selector:
                        continue
                    try:
                        name_field = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        name_field.clear()
                        name_field.send_keys("AI Summarizer")
                        name_entered = True
                        logger.info(
                            "[Google Meet] Entered bot name via %s='%s'.",
                            by,
                            selector,
                        )
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue

                if not name_entered:
                    logger.debug(
                        "[Google Meet] No name field found – likely signed in."
                    )

                # Small pause to let the "Ask to join" button become enabled
                # after the name is entered.
                time.sleep(1)

                # Mute mic and camera before joining
                self._safe_click(wait, sel.get("mute_mic", ""), By.CSS_SELECTOR)
                self._safe_click(wait, sel.get("mute_cam", ""), By.CSS_SELECTOR)

                # ── Click join button ────────────────────────────────────
                # Try multiple strategies: XPath text match is the most
                # reliable for Google Meet since jsname attrs change often.
                joined = False
                join_strategies = [
                    # Strategy 1: XPath by visible button text
                    (By.XPATH, "//button[.//span[text()='Ask to join']]"),
                    (By.XPATH, "//button[contains(., 'Ask to join')]"),
                    (By.XPATH, "//button[.//span[text()='Join now']]"),
                    (By.XPATH, "//button[contains(., 'Join now')]"),
                    # Strategy 2: CSS selectors from config
                    (By.CSS_SELECTOR, sel.get("ask_to_join_button", "")),
                    (By.CSS_SELECTOR, sel.get("join_now_button", "")),
                ]
                for by, selector in join_strategies:
                    if not selector:
                        continue
                    try:
                        join_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        join_btn.click()
                        logger.info(
                            "[Google Meet] Clicked join via %s='%s' on attempt %d.",
                            by,
                            selector,
                            attempt,
                        )
                        joined = True
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue

                if not joined:
                    raise TimeoutException(
                        "Neither 'Ask to join' nor 'Join now' button found."
                    )

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
                logger.info(
                    "[Zoom] Attempt %d/%d – navigating to %s",
                    attempt,
                    self.retry_limit,
                    link,
                )
                self.driver.get(link)

                wait = WebDriverWait(self.driver, 15)

                # Enter display name
                name_field = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, sel.get("name_field", "#inputname"))
                    )
                )
                name_field.clear()
                name_field.send_keys("AI Meeting Assistant")

                # Click Join
                join_btn = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            sel.get("join_button", ".preview-join-button"),
                        )
                    )
                )
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
                logger.info(
                    "[Teams] Attempt %d/%d – navigating to %s",
                    attempt,
                    self.retry_limit,
                    link,
                )
                self.driver.get(link)

                wait = WebDriverWait(self.driver, 15)

                # Bypass "Open app" prompt – choose "Continue on this browser"
                use_browser = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            sel.get("use_browser_link", "a[data-tid='joinOnWeb']"),
                        )
                    )
                )
                use_browser.click()

                # Continue without audio/video if prompted
                self._safe_click(
                    wait,
                    sel.get("continue_without_audio", "[data-tid='prejoin-ok-cta']"),
                    By.CSS_SELECTOR,
                )

                # Mute mic
                self._safe_click(
                    wait,
                    sel.get("mute_mic", "[data-tid='toggle-mute']"),
                    By.CSS_SELECTOR,
                )

                # Join call
                join_btn = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            sel.get("join_button", "[data-tid='call-join-button']"),
                        )
                    )
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
        """Return True if an end-screen element is found in the DOM.

        This checks for hard "meeting ended" signals only (host ended,
        page navigation).  The softer "alone in meeting" detection is
        handled separately by :meth:`_is_alone_in_meeting`.
        """
        # Google Meet: data-call-ended attribute (T021)
        if self.detected_platform == "google_meet":
            try:
                self.driver.find_element(By.CSS_SELECTOR, "[data-call-ended='true']")
                return True
            except NoSuchElementException:
                pass
            # Also check if we were kicked out / redirected
            try:
                current_url = self.driver.current_url
                if "meet.google.com" not in current_url:
                    logger.info("Redirected away from Meet — meeting ended.")
                    return True
            except Exception:  # noqa: BLE001
                pass

        # Zoom: URL change or disconnect dialog (T022)
        if self.detected_platform == "zoom":
            current_url = self.driver.current_url
            if "meeting/end" in current_url or "reason=ended" in current_url:
                return True
            try:
                dialog = self.driver.find_element(
                    By.CSS_SELECTOR, ".zm-modal-body-title"
                )
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
    # Alone-in-meeting detection (Google Meet)
    # ──────────────────────────────────────────────────────────

    def _is_alone_in_meeting(self, platform_sel: dict) -> bool:
        """Return True if the agent appears to be the only participant.

        Uses multiple layered strategies, from most reliable to least:

        1. **``driver.page_source``** (Python-level) — searches the raw HTML
           of the entire page for known "alone" text patterns.  This catches
           text regardless of visibility, Shadow DOM, or JS rendering.

        2. **``[role='alert']`` elements** (JS) — Google Meet renders the
           "No one else is in this meeting" banner as a toast with
           ``role="alert"`` or ``role="status"``.

        3. **``textContent`` search** (JS) — searches ALL text in the DOM
           including hidden / off-screen elements (unlike ``innerText``
           which only returns visible text).

        4. **Participant tile count** (JS) — counts elements with
           ``[data-participant-id]``.  If ≤ 1, we are alone.

        Either signal returning True is sufficient.
        """
        if self.detected_platform != "google_meet":
            return False

        # Patterns that indicate the agent is alone
        _ALONE_PATTERNS = [
            "No one else is in this meeting",
            "You're the only one here",
            "You are the only one here",
        ]

        # ── Strategy 1: driver.page_source (Python-level HTML search) ──
        # This is the most reliable method — it gets the COMPLETE raw HTML
        # directly from Chrome, including hidden elements, overlays, toasts,
        # and dynamically-rendered content.
        try:
            page_src = self.driver.page_source
            for pattern in _ALONE_PATTERNS:
                if pattern in page_src:
                    logger.info(
                        "Alone detected via page_source: found '%s'.", pattern
                    )
                    return True
        except Exception as exc:  # noqa: BLE001
            logger.debug("page_source check failed: %s", exc)

        # ── Strategy 2-4: JavaScript-based checks (single call) ────────
        try:
            result = self.driver.execute_script("""
                var debug = {};

                // ── Strategy 2: role="alert" / role="status" elements ──
                // Google Meet shows the "No one else" banner as a toast
                // notification with role="alert".
                var alertEls = document.querySelectorAll(
                    '[role="alert"], [role="status"], [role="marquee"]'
                );
                debug.alertCount = alertEls.length;
                debug.alertTexts = [];
                for (var i = 0; i < alertEls.length; i++) {
                    var txt = alertEls[i].textContent || '';
                    debug.alertTexts.push(txt.substring(0, 100));
                    if (txt.indexOf('No one else') !== -1 ||
                        txt.indexOf('only one here') !== -1 ||
                        txt.indexOf('the only one') !== -1) {
                        return {alone: true, reason: 'alert_role', debug: debug};
                    }
                }

                // ── Strategy 3: textContent search (hidden + visible) ──
                // textContent includes ALL text nodes, even hidden ones
                // (unlike innerText which only returns visible text).
                var bodyText = document.body.textContent || '';
                debug.textLength = bodyText.length;
                debug.textSnippet = bodyText.substring(0, 200);

                var patterns = [
                    'No one else is in this meeting',
                    "You're the only one here",
                    'You are the only one here',
                ];
                for (var j = 0; j < patterns.length; j++) {
                    if (bodyText.indexOf(patterns[j]) !== -1) {
                        return {alone: true, reason: 'textContent', debug: debug};
                    }
                }

                // ── Strategy 4: Count participant video tiles ──────────
                var tiles = document.querySelectorAll(
                    '[data-participant-id], [data-requested-participant-id]'
                );
                debug.tileCount = tiles.length;

                // Also count visible tiles
                var visibleTiles = 0;
                for (var k = 0; k < tiles.length; k++) {
                    if (tiles[k].offsetParent !== null) visibleTiles++;
                }
                debug.visibleTiles = visibleTiles;

                if (tiles.length === 1 || (tiles.length > 0 && visibleTiles === 1)) {
                    return {alone: true, reason: 'single_tile', debug: debug};
                }

                // ── Strategy 5: Check for "Just you" in People panel ──
                // Even when the panel is closed, the DOM may contain this
                if (bodyText.indexOf('Just you') !== -1) {
                    return {alone: true, reason: 'just_you_text', debug: debug};
                }

                return {alone: false, reason: 'none', debug: debug};
            """)

            if result:
                debug_info = result.get("debug", {})
                if result.get("alone"):
                    logger.info(
                        "Alone detected via JS (reason=%s) | "
                        "tiles=%s visible=%s alerts=%s",
                        result.get("reason"),
                        debug_info.get("tileCount"),
                        debug_info.get("visibleTiles"),
                        debug_info.get("alertCount"),
                    )
                    return True
                else:
                    # Log debug info so we can diagnose why detection failed
                    logger.debug(
                        "Not alone | tiles=%s visible=%s alerts=%s "
                        "alertTexts=%s textSnippet='%s'",
                        debug_info.get("tileCount"),
                        debug_info.get("visibleTiles"),
                        debug_info.get("alertCount"),
                        debug_info.get("alertTexts"),
                        str(debug_info.get("textSnippet", ""))[:100],
                    )

        except Exception as exc:  # noqa: BLE001
            logger.warning("JS alone-detection error: %s", exc)

        return False

    # ──────────────────────────────────────────────────────────
    # Leave-call helper
    # ──────────────────────────────────────────────────────────

    def _click_leave_button(self) -> None:
        """Attempt to click the platform's leave/hang-up button.

        For Google Meet this is the red phone icon at the bottom.
        Failing silently is fine — the browser quit() will forcefully
        disconnect anyway.
        """
        if self.detected_platform == "google_meet":
            sel = self.selectors.get("google_meet", {})
            leave_strategies = [
                # Config-driven selector
                (By.CSS_SELECTOR, sel.get("leave_call_button", "")),
                # XPath by aria-label
                (By.XPATH, "//button[@aria-label='Leave call']"),
                (By.XPATH, "//button[contains(@aria-label, 'Leave')]"),
                # The red hang-up icon is often inside a specific jsname
                (By.CSS_SELECTOR, "button[jsname='CQylAd']"),
                # data-tooltip fallback
                (By.CSS_SELECTOR, "[data-tooltip='Leave call']"),
            ]
            for by, selector in leave_strategies:
                if not selector:
                    continue
                try:
                    btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    btn.click()
                    logger.info(
                        "[Google Meet] Clicked leave button via %s='%s'.",
                        by,
                        selector,
                    )
                    return
                except (TimeoutException, NoSuchElementException):
                    continue
            logger.warning("[Google Meet] Could not find leave button.")

        elif self.detected_platform == "teams":
            sel = self.selectors.get("teams", {})
            try:
                btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, sel.get("leave_call_button", "[data-tid='leave-call-btn']"))
                    )
                )
                btn.click()
                logger.info("[Teams] Clicked leave button.")
            except (TimeoutException, NoSuchElementException):
                logger.warning("[Teams] Could not find leave button.")

    # ──────────────────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────────────────

    def _safe_click(
        self, wait: WebDriverWait, selector: str, by: str = By.CSS_SELECTOR
    ) -> None:
        """Click an element if it is present; silently skip if absent."""
        if not selector:
            return
        try:
            el = wait.until(EC.element_to_be_clickable((by, selector)))
            el.click()
        except (TimeoutException, NoSuchElementException):
            pass
