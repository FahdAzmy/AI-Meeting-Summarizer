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
        r"https?://(?:teams\.microsoft\.com/l/meetup-join/[^\s]+|teams\.live\.com/meet/[^\s]+)",
        re.IGNORECASE,
    ),
    "zoom_sdk": re.compile(r"https?://localhost:\d+/zoom-meeting.*", re.IGNORECASE),
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
            "zoom_sdk": self._join_zoom_sdk,
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

        # ── Teams: Wait for lobby admission first ─────────────────────────
        # After clicking "Join now", Teams may put the bot in a waiting room.
        # We wait here (up to 5 min) for the host to admit the bot before
        # starting the main meeting-end polling loop.
        if self.detected_platform == "teams":
            _LOBBY_PHRASES = [
                "someone will let you in",
                "waiting to be let in",
                "waiting to be admitted",
                "let you in shortly",
                "please wait",
            ]
            _LOBBY_END_PHRASES = [
                "the meeting has ended",
                "you have left the meeting",
                "meeting has been cancelled",
                "enjoy your call?",
            ]
            lobby_timeout = 300
            lobby_start = time.time()
            in_lobby = False

            # Brief pause to let the page transition after clicking Join
            time.sleep(3)

            while time.time() - lobby_start < lobby_timeout:
                try:
                    page_src = self.driver.page_source.lower()
                except Exception:
                    break

                # Check if meeting ended while in lobby
                if any(p in page_src for p in _LOBBY_END_PHRASES):
                    logger.warning("[Teams] Meeting ended while in lobby.")
                    return  # exit — meeting is over

                # Check if still in lobby
                if any(p in page_src for p in _LOBBY_PHRASES):
                    if not in_lobby:
                        in_lobby = True
                        logger.info(
                            "[Teams] Bot is in lobby. Waiting for admission "
                            "(timeout=%ds)…", lobby_timeout,
                        )
                    logger.debug(
                        "[Teams] Still in lobby… (%ds / %ds)",
                        int(time.time() - lobby_start), lobby_timeout,
                    )
                    time.sleep(5)
                else:
                    if in_lobby:
                        logger.info(
                            "[Teams] Admitted from lobby after %ds.",
                            int(time.time() - lobby_start),
                        )
                    else:
                        logger.info("[Teams] No lobby — joined directly.")
                    break
            else:
                logger.error(
                    "[Teams] Lobby timeout (%ds) — host never admitted.",
                    lobby_timeout,
                )
                return  # exit — give up waiting

        alone_since: float | None = None  # timestamp when we first detected alone
        poll_count = 0
        meeting_start = time.time()
        # Minimum time (seconds) to stay in the meeting before allowing
        # "alone" detection to trigger an exit.  This prevents the bot from
        # leaving immediately after joining when it's the first participant.
        MIN_MEETING_DURATION = 30

        while True:
            poll_count += 1
            elapsed_in_meeting = int(time.time() - meeting_start)
            logger.info(
                "Poll #%d | Checking meeting status (platform=%s) | in-meeting %ds…",
                poll_count,
                self.detected_platform,
                elapsed_in_meeting,
            )

            # ── Check 1: Host ended the meeting (hard signal) ─────────────
            # This is always checked — if the host explicitly ends the
            # meeting, we leave immediately regardless of duration.
            if self._meeting_has_ended(end_xpath):
                logger.info(
                    "Meeting end detected (end screen) after %ds. Exiting wait loop.",
                    elapsed_in_meeting,
                )
                return

            # ── Check 2: Agent is alone in the meeting ───────────────────
            # Skip this check during the warm-up period to avoid false
            # positives (e.g. bot is first to join, "Waiting for others").
            if elapsed_in_meeting < MIN_MEETING_DURATION:
                logger.debug(
                    "Warm-up period (%ds/%ds) — skipping alone check.",
                    elapsed_in_meeting,
                    MIN_MEETING_DURATION,
                )
            else:
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
        # Block Chrome's native "Open Zoom Meetings?" protocol-handler prompt.
        # Chrome raises this dialog when the page redirects to zoommtg://..
        # Selenium cannot interact with native OS dialogs, so we suppress it
        # at the Chrome preference level before any page is loaded.
        prefs = {
            "protocol_handler": {
                "excluded_schemes": {
                    "zoommtg": True,
                    "zoomus": True,
                    "zoom": True,
                }
            }
        }
        options.add_experimental_option("prefs", prefs)
        if headless:
            options.add_argument("--headless=new")
        return options

    @staticmethod
    def _teams_web_url(link: str) -> str:
        """Rewrite a ``teams.live.com/meet/`` short link to the v2 web deep-link
        that opens the pre-join page directly in the browser without the
        "Open Teams app?" native-app redirect.

        Example::
            https://teams.live.com/meet/9362297015184?p=y7BwyN5fArqTg1vBql
            → https://teams.live.com/v2/#/meet/9362297015184?p=y7BwyN5fArqTg1vBql&anon=true&launchType=web

        For ``teams.microsoft.com`` URLs the link is returned unchanged.
        """
        import urllib.parse

        parsed = urllib.parse.urlparse(link)
        if "teams.live.com" not in parsed.netloc:
            return link  # enterprise URLs use the old flow

        # Extract meeting ID from /meet/<ID>
        m = re.match(r"/meet/([^/?#]+)", parsed.path)
        if not m:
            logger.warning("[Teams] Could not parse meeting ID from: %s", link)
            return link

        meeting_id = m.group(1)
        # Preserve the original query string (e.g. p=...) and append web params
        qs = parsed.query  # e.g. "p=y7BwyN5fArqTg1vBql"
        extra = "anon=true&launchType=web"
        full_qs = f"{qs}&{extra}" if qs else extra
        web_url = f"https://teams.live.com/v2/#/meet/{meeting_id}?{full_qs}"
        logger.info("[Teams] Rewrote URL to web deep-link: %s", web_url)
        return web_url

    @staticmethod
    def _zoom_web_client_url(link: str) -> str:
        """Rewrite a standard Zoom meeting URL to the web-client join URL.

        Example::
            https://us05web.zoom.us/j/12345678900?pwd=abc
            → https://us05web.zoom.us/wc/12345678900/join?pwd=abc

        The web-client URL loads Zoom directly in the browser without
        triggering the protocol-handler popup, so no "Cancel" click is needed.
        Returns the original link unchanged if it cannot be parsed.
        """
        import urllib.parse

        parsed = urllib.parse.urlparse(link)
        # Match paths like /j/12345678900
        m = re.match(r"/j/(\d+)", parsed.path)
        if not m:
            return link  # fallback – return as-is
        meeting_id = m.group(1)
        new_path = f"/wc/{meeting_id}/join"
        web_url = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc, new_path, "", parsed.query, "")
        )
        logger.info("[Zoom] Rewrote URL to web client: %s", web_url)
        return web_url

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
        # Rewrite to Zoom web-client URL – this bypasses the OS protocol-handler
        # popup ("Open Zoom Meetings?") entirely. Chrome's zoommtg:// scheme is
        # also blocked via Chrome prefs set in _build_chrome_options.
        web_link = self._zoom_web_client_url(link)
        for attempt in range(1, self.retry_limit + 1):
            self.current_attempt = attempt
            try:
                logger.info(
                    "[Zoom] Attempt %d/%d – navigating to web client: %s",
                    attempt,
                    self.retry_limit,
                    web_link,
                )
                self.driver.get(web_link)

                # ── Wait for the "Enter Meeting Info" page to render ─────────
                # The /wc/ SPA loads fast — 5 seconds is enough for the controls
                # (mic toggle, name field, Join button) to become interactive.
                time.sleep(5)

                BOT_NAME = "AI Summarizer"

                # ── Mute mic, fill name, click Join — all via JS ─────────────
                # Using a single execute_script is the fastest path: no polling,
                # no per-selector timeouts. The mic button on this page shows
                # "Mute" when active (click it to mute). Camera is already off
                # ("Start Video" button), so we leave it alone.
                self.driver.execute_script(
                    """
                    var botName = arguments[0];

                    // 1. Mute microphone – button whose text is exactly "Mute"
                    var btns = document.querySelectorAll('button');
                    for (var i = 0; i < btns.length; i++) {
                        var t = (btns[i].innerText || btns[i].textContent || '').trim();
                        if (t === 'Mute') { btns[i].click(); break; }
                    }

                    // 2. Fill the name input
                    var inputs = document.querySelectorAll('input[type="text"], input:not([type])');
                    for (var j = 0; j < inputs.length; j++) {
                        if (inputs[j].offsetParent !== null) {
                            // Use React's native setter so the component state updates
                            var setter = Object.getOwnPropertyDescriptor(
                                window.HTMLInputElement.prototype, 'value').set;
                            setter.call(inputs[j], botName);
                            inputs[j].dispatchEvent(new Event('input',  { bubbles: true }));
                            inputs[j].dispatchEvent(new Event('change', { bubbles: true }));
                            break;
                        }
                    }
                    """,
                    BOT_NAME,
                )
                logger.info("[Zoom] Muted mic and entered name '%s' via JS.", BOT_NAME)

                # Brief pause so React re-renders the Join button as enabled
                time.sleep(0.5)

                # ── Click Join ───────────────────────────────────────────────
                # Try DOM selector first, fall back to JS text search.
                joined = False
                for by, selector in [
                    (By.XPATH, "//button[normalize-space(text())='Join']"),
                    (By.XPATH, "//button[.//span[normalize-space(text())='Join']]"),
                    (By.CSS_SELECTOR, sel.get("join_button", "")),
                ]:
                    if not selector:
                        continue
                    try:
                        join_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        join_btn.click()
                        logger.info("[Zoom] Clicked Join via %s='%s'.", by, selector)
                        joined = True
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue

                if not joined:
                    self.driver.execute_script(
                        """
                        var btns = document.querySelectorAll('button');
                        for (var i = 0; i < btns.length; i++) {
                            var t = (btns[i].innerText || btns[i].textContent || '').trim();
                            if (t === 'Join') { btns[i].click(); break; }
                        }
                    """
                    )
                    logger.info("[Zoom] Clicked Join via JS fallback.")

                # Detect and handle waiting room
                wait = WebDriverWait(self.driver, 15)
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
    # Zoom SDK join logic (US1 / US4)
    # ──────────────────────────────────────────────────────────

    def _join_zoom_sdk(self, link: str) -> None:
        """The React background page handles joining automatically. Just load it."""
        logger.info("[Zoom SDK] Loading background page: %s", link)
        self.driver.get(link)
        logger.info("[Zoom SDK] Background page loaded. The SDK will handle the rest.")

    # ──────────────────────────────────────────────────────────
    # MS Teams join logic (US1 – T017)
    # ──────────────────────────────────────────────────────────

    def _join_teams(self, link: str) -> None:
        """Join an MS Teams meeting.

        Supports both:
        * ``teams.live.com/meet/<ID>`` — personal/consumer meetings.
          Rewrites to ``/v2/#/meet/`` deep-link (pre-join page, no app redirect).
        * ``teams.microsoft.com/l/meetup-join/…`` — enterprise/work meetings.
          Uses the old selector-driven flow ("Continue on this browser").

        Live URL pre-join sequence (matching the UI in the screenshot):
        1. Navigate to rewritten URL.
        2. Wait 5 s for the SPA to render.
        3. Select "Don't use audio".
        4. Turn camera OFF.
        5. Enter bot name "AI Summarizer".
        6. Click "Join now".
        """
        sel = self.selectors.get("teams", {})
        BOT_NAME = "AI Summarizer"
        is_live_url = "teams.live.com" in link

        for attempt in range(1, self.retry_limit + 1):
            self.current_attempt = attempt
            try:
                nav_link = self._teams_web_url(link)
                logger.info(
                    "[Teams] Attempt %d/%d – navigating to %s",
                    attempt,
                    self.retry_limit,
                    nav_link,
                )
                self.driver.get(nav_link)

                wait = WebDriverWait(self.driver, 25)

                if is_live_url:
                    # ── 1. Wait for SPA pre-join page to render ──────────────
                    logger.info("[Teams] Waiting 20 s for pre-join SPA to render…")
                    time.sleep(20)

                    # ── 2. Keep "Computer audio" and mute microphone ─────────
                    # "Computer audio" is selected by default. We ensure it's
                    # active (so OBS can capture meeting audio), then turn OFF
                    # the microphone toggle so the bot doesn't transmit noise.

                    # 2a. Ensure "Computer audio" radio is selected (safety click)
                    try:
                        self.driver.execute_script(
                            """
                            var radios = document.querySelectorAll('input[type="radio"]');
                            for (var i = 0; i < radios.length; i++) {
                                var p = radios[i].closest('label') || radios[i].parentElement;
                                var txt = p ? (p.textContent || '').toLowerCase() : '';
                                if (txt.indexOf('computer audio') !== -1) {
                                    if (!radios[i].checked) { radios[i].click(); }
                                    return;
                                }
                            }
                        """
                        )
                        logger.info("[Teams] Ensured 'Computer audio' is selected.")
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("[Teams] Computer audio selection failed: %s", exc)

                    time.sleep(0.5)

                    # 2b. Turn OFF the microphone toggle switch
                    mic_muted = False
                    for by, sel_str in [
                        (By.CSS_SELECTOR, "[data-tid='toggle-mute']"),
                        (By.CSS_SELECTOR, "[data-tid='prejoin-audio-mute']"),
                        (By.CSS_SELECTOR, "[aria-label*='microphone' i][role='switch']"),
                        (By.CSS_SELECTOR, "[aria-label*='microphone' i][role='checkbox']"),
                        (By.CSS_SELECTOR, "[aria-label*='mic' i][role='switch']"),
                        (By.CSS_SELECTOR, "[aria-label*='mic' i][role='checkbox']"),
                        (By.CSS_SELECTOR, "[aria-label*='mute' i][role='switch']"),
                        (By.CSS_SELECTOR, "[aria-label*='mute' i][role='checkbox']"),
                    ]:
                        try:
                            el = WebDriverWait(self.driver, 2).until(
                                EC.presence_of_element_located((by, sel_str))
                            )
                            # If the toggle is ON (checked/true), click to turn OFF
                            is_on = (
                                el.get_attribute("aria-checked") == "true"
                                or el.get_attribute("checked") == "true"
                            )
                            if is_on:
                                el.click()
                                logger.info("[Teams] Muted microphone via %s", sel_str)
                            else:
                                logger.info("[Teams] Microphone already muted (%s)", sel_str)
                            mic_muted = True
                            break
                        except (TimeoutException, NoSuchElementException):
                            continue

                    if not mic_muted:
                        # JS fallback: find the mic toggle by scanning switches
                        try:
                            self.driver.execute_script(
                                """
                                // Look for toggle switches related to microphone
                                var toggles = document.querySelectorAll(
                                    '[role="switch"], [role="checkbox"], input[type="checkbox"]'
                                );
                                for (var i = 0; i < toggles.length; i++) {
                                    var el = toggles[i];
                                    var label = (el.getAttribute('aria-label') || '').toLowerCase();
                                    var tid = (el.getAttribute('data-tid') || '').toLowerCase();
                                    if (label.indexOf('mic') !== -1 || label.indexOf('mute') !== -1 ||
                                        tid.indexOf('mic') !== -1 || tid.indexOf('mute') !== -1) {
                                        if (el.checked || el.getAttribute('aria-checked') === 'true') {
                                            el.click();
                                        }
                                        return;
                                    }
                                }
                            """
                            )
                            logger.info("[Teams] Mic toggle clicked (JS fallback).")
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("[Teams] JS mic toggle failed: %s", exc)
                    time.sleep(1)

                    # ── 3. Turn camera OFF ────────────────────────────────────
                    camera_toggled = False
                    for by, sel_str in [
                        (By.CSS_SELECTOR, "[data-tid='toggle-video']"),
                        (By.CSS_SELECTOR, "[data-tid='prejoin-video-toggle']"),
                        (By.CSS_SELECTOR, "[aria-label*='camera' i][role='switch']"),
                        (By.CSS_SELECTOR, "[aria-label*='camera' i][role='checkbox']"),
                        (By.CSS_SELECTOR, "[aria-label*='video' i][role='switch']"),
                        (By.CSS_SELECTOR, "[aria-label*='video' i][role='checkbox']"),
                    ]:
                        try:
                            el = WebDriverWait(self.driver, 1).until(
                                EC.presence_of_element_located((by, sel_str))
                            )
                            is_checked = (
                                el.get_attribute("aria-checked") == "true"
                                or el.get_attribute("checked") == "true"
                            )
                            if is_checked:
                                el.click()
                                logger.info("[Teams] Turned camera OFF via %s", sel_str)
                            else:
                                logger.info("[Teams] Camera already OFF (%s)", sel_str)
                            camera_toggled = True
                            break
                        except (TimeoutException, NoSuchElementException):
                            continue

                    if not camera_toggled:
                        try:
                            self.driver.execute_script(
                                """
                                var toggles = document.querySelectorAll('input[type="checkbox"], [role="switch"], [role="checkbox"]');
                                for (var j = 0; j < toggles.length; j++) {
                                    var el = toggles[j];
                                    var tl = (el.getAttribute('aria-label') || '').toLowerCase();
                                    var id = (el.id || '').toLowerCase();
                                    var dataTid = (el.getAttribute('data-tid') || '').toLowerCase();
                                    
                                    if (tl.indexOf('camera') !== -1 || tl.indexOf('video') !== -1 ||
                                        id.indexOf('camera') !== -1 || id.indexOf('video') !== -1 ||
                                        dataTid.indexOf('camera') !== -1 || dataTid.indexOf('video') !== -1) {
                                        
                                        if (el.checked || el.getAttribute('aria-checked') === 'true') {
                                            el.click();
                                        }
                                        return;
                                    }
                                }
                                // If we couldn't find a label, the first toggle on the page is usually the camera.
                                // We click it if it's currently ON.
                                if (toggles.length > 0) {
                                    var firstToggle = toggles[0];
                                    if (firstToggle.checked || firstToggle.getAttribute('aria-checked') === 'true') {
                                        firstToggle.click();
                                    }
                                }
                            """
                            )
                            logger.info("[Teams] Camera toggle clicked (JS fallback).")
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("[Teams] Camera toggle JS failed: %s", exc)
                    time.sleep(1)

                    # ── 4. Enter bot name ────────────────────────────────────
                    name_entered = False
                    for by, sel_str in [
                        (By.XPATH, "//input[@placeholder='Type your name']"),
                        (By.XPATH, "//input[contains(@placeholder,'name')]"),
                        (By.CSS_SELECTOR, "input[placeholder*='name']"),
                        (By.CSS_SELECTOR, "input[type='text']"),
                        (By.CSS_SELECTOR, sel.get("name_field", "")),
                    ]:
                        if not sel_str:
                            continue
                        try:
                            field = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((by, sel_str))
                            )
                            field.clear()
                            field.send_keys(BOT_NAME)
                            name_entered = True
                            logger.info(
                                "[Teams] Entered name '%s' via %s='%s'.",
                                BOT_NAME,
                                by,
                                sel_str,
                            )
                            break
                        except (TimeoutException, NoSuchElementException):
                            continue

                    if not name_entered:
                        # React-native-setter JS fallback
                        try:
                            self.driver.execute_script(
                                """
                                var name = arguments[0];
                                var inputs = document.querySelectorAll(
                                    'input[type="text"], input:not([type])');
                                for (var i = 0; i < inputs.length; i++) {
                                    if (inputs[i].offsetParent !== null) {
                                        var setter = Object.getOwnPropertyDescriptor(
                                            window.HTMLInputElement.prototype, 'value').set;
                                        setter.call(inputs[i], name);
                                        inputs[i].dispatchEvent(
                                            new Event('input',  { bubbles: true }));
                                        inputs[i].dispatchEvent(
                                            new Event('change', { bubbles: true }));
                                        break;
                                    }
                                }
                            """,
                                BOT_NAME,
                            )
                            name_entered = True
                            logger.info("[Teams] Entered name via JS React fallback.")
                        except Exception as exc:  # noqa: BLE001
                            logger.warning("[Teams] JS name entry failed: %s", exc)

                    if not name_entered:
                        logger.warning("[Teams] Could not enter bot name – continuing.")

                    # Brief pause so "Join now" activates after name entry
                    time.sleep(1)

                    # ── 5. Click "Join now" ───────────────────────────────────
                    joined = False
                    for by, sel_str in [
                        (By.XPATH, "//button[normalize-space(.)='Join now']"),
                        (By.XPATH, "//button[contains(.,'Join now')]"),
                        (By.XPATH, "//button[contains(.,'Join Now')]"),
                        (By.CSS_SELECTOR, "[data-tid='prejoin-join-button']"),
                        (By.CSS_SELECTOR, sel.get("join_button", "")),
                    ]:
                        if not sel_str:
                            continue
                        try:
                            btn = WebDriverWait(self.driver, 8).until(
                                EC.element_to_be_clickable((by, sel_str))
                            )
                            btn.click()
                            logger.info(
                                "[Teams] Clicked 'Join now' via %s='%s'.", by, sel_str
                            )
                            joined = True
                            break
                        except (TimeoutException, NoSuchElementException):
                            continue

                    if not joined:
                        # JS last-resort: scan buttons by text
                        self.driver.execute_script(
                            """
                            var btns = document.querySelectorAll('button');
                            for (var i = 0; i < btns.length; i++) {
                                var t = (btns[i].innerText ||
                                         btns[i].textContent || '').trim();
                                if (t === 'Join now' || t === 'Join Now') {
                                    btns[i].click(); return;
                                }
                            }
                        """
                        )
                        logger.info("[Teams] Clicked 'Join now' via JS last-resort.")

                else:
                    # ── Enterprise Teams flow (teams.microsoft.com) ───────────
                    use_browser = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                sel.get("use_browser_link", "a[data-tid='joinOnWeb']"),
                            )
                        )
                    )
                    use_browser.click()

                    self._safe_click(
                        wait,
                        sel.get(
                            "continue_without_audio", "[data-tid='prejoin-ok-cta']"
                        ),
                        By.CSS_SELECTOR,
                    )
                    self._safe_click(
                        wait,
                        sel.get("mute_mic", "[data-tid='toggle-mute']"),
                        By.CSS_SELECTOR,
                    )

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

        # MS Teams: specific text phrases indicating meeting ended
        if self.detected_platform == "teams":
            try:
                page_src = self.driver.page_source
                _TEAMS_END_PHRASES = [
                    "The meeting has ended",
                    "You have left the meeting",
                    "Enjoy your call?",
                    "Rejoin the call",
                    "Did you leave by mistake?",
                    "Your meeting has expired",
                ]
                for phrase in _TEAMS_END_PHRASES:
                    if phrase in page_src:
                        logger.info(
                            "[Teams] Meeting ended — found phrase: '%s'", phrase
                        )
                        return True
            except Exception:
                pass
            # NOTE: We intentionally do NOT check URL redirects for Teams.
            # After joining, Teams changes the URL (e.g. from /meet/ to
            # /calling/) which caused false positives.

        # Zoom SDK: React page status check
        if self.detected_platform == "zoom_sdk":
            try:
                page_src = self.driver.page_source
                if "Meeting ended" in page_src:
                    return True
            except Exception:
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
        if self.detected_platform not in ("google_meet", "teams"):
            return False

        # Teams: if the bot is still in the lobby, it's NOT "alone in meeting"
        if self.detected_platform == "teams":
            try:
                page_lower = self.driver.page_source.lower()
                _LOBBY_INDICATORS = [
                    "someone will let you in",
                    "waiting to be let in",
                    "waiting to be admitted",
                    "let you in shortly",
                ]
                if any(ind in page_lower for ind in _LOBBY_INDICATORS):
                    logger.debug(
                        "[Teams] Bot is still in lobby — not checking alone status."
                    )
                    return False
            except Exception:
                pass

        # Patterns that indicate the agent is alone
        if self.detected_platform == "google_meet":
            _ALONE_PATTERNS = [
                "No one else is in this meeting",
                "You're the only one here",
                "You are the only one here",
                "Just you",
            ]
        elif self.detected_platform == "teams":
            _ALONE_PATTERNS = [
                "Waiting for others to join",
                "Waiting for people to join",
                "You're the only one in the meeting",
                "You are the only one in the meeting",
                "You're the only one here",
                "You are the only one here",
            ]
        else:
            _ALONE_PATTERNS = []

        # ── Strategy 1: driver.page_source (Python-level HTML search) ──
        # This is the most reliable method — it gets the COMPLETE raw HTML
        # directly from Chrome, including hidden elements, overlays, toasts,
        # and dynamically-rendered content.
        try:
            page_src = self.driver.page_source
            for pattern in _ALONE_PATTERNS:
                if pattern in page_src:
                    logger.info("Alone detected via page_source: found '%s'.", pattern)
                    return True
        except Exception as exc:  # noqa: BLE001
            logger.debug("page_source check failed: %s", exc)

        # ── Strategy 2-4: JavaScript-based checks (single call) ────────
        try:
            result = self.driver.execute_script(
                """
                var patterns = arguments[0];
                var debug = {};

                // ── Strategy 2: role="alert" / role="status" elements ──
                var alertEls = document.querySelectorAll(
                    '[role="alert"], [role="status"], [role="marquee"]'
                );
                debug.alertCount = alertEls.length;
                debug.alertTexts = [];
                for (var i = 0; i < alertEls.length; i++) {
                    var txt = alertEls[i].textContent || '';
                    debug.alertTexts.push(txt.substring(0, 100));
                    for (var j = 0; j < patterns.length; j++) {
                        if (txt.indexOf(patterns[j]) !== -1) {
                            return {alone: true, reason: 'alert_role', debug: debug};
                        }
                    }
                }

                // ── Strategy 3: textContent search (hidden + visible) ──
                // textContent includes ALL text nodes, even hidden ones
                // (unlike innerText which only returns visible text).
                var bodyText = document.body.textContent || '';
                debug.textLength = bodyText.length;
                debug.textSnippet = bodyText.substring(0, 200);

                for (var j = 0; j < patterns.length; j++) {
                    if (bodyText.indexOf(patterns[j]) !== -1) {
                        return {alone: true, reason: 'textContent', debug: debug};
                    }
                }

                // ── Strategy 4: Count participant video tiles (Meet only) ──
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

                return {alone: false, reason: 'none', debug: debug};
            """,
                _ALONE_PATTERNS,
            )

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
                        (
                            By.CSS_SELECTOR,
                            sel.get("leave_call_button", "[data-tid='leave-call-btn']"),
                        )
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
