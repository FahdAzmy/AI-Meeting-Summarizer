"""Meeting monitoring and leave helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .constants import ALONE_PATTERNS, LOBBY_END_PHRASES, LOBBY_PHRASES, TEAMS_END_PHRASES

if TYPE_CHECKING:
    from modules.meeting_access import MeetingAccess

logger = logging.getLogger(__name__)


def wait_for_teams_lobby(access: "MeetingAccess", *, lobby_timeout: int = 300) -> None:
    """Wait for Teams lobby admission before end polling begins."""
    lobby_start = access._now()
    in_lobby = False

    access._sleep(3)

    while access._now() - lobby_start < lobby_timeout:
        try:
            page_src = access.driver.page_source.lower()
        except Exception:
            break

        if any(phrase in page_src for phrase in LOBBY_END_PHRASES):
            logger.warning("[Teams] Meeting ended while in lobby.")
            return

        if any(phrase in page_src for phrase in LOBBY_PHRASES):
            if not in_lobby:
                in_lobby = True
                logger.info(
                    "[Teams] Bot is in lobby. Waiting for admission (timeout=%ds)...",
                    lobby_timeout,
                )
            logger.debug(
                "[Teams] Still in lobby... (%ds / %ds)",
                int(access._now() - lobby_start),
                lobby_timeout,
            )
            access._sleep(5)
        else:
            if in_lobby:
                logger.info("[Teams] Admitted from lobby after %ds.", int(access._now() - lobby_start))
            else:
                logger.info("[Teams] No lobby - joined directly.")
            break
    else:
        logger.error("[Teams] Lobby timeout (%ds) - host never admitted.", lobby_timeout)
        raise TimeoutException("Waiting room timeout - host never admitted the bot.")


def meeting_has_ended(access: "MeetingAccess", end_xpath: str) -> bool:
    """Return True when platform-specific or generic end signals are present."""
    platform = access.platform_key

    if platform == "google_meet":
        try:
            access.driver.find_element(By.CSS_SELECTOR, "[data-call-ended='true']")
            return True
        except NoSuchElementException:
            pass
        try:
            current_url = access.driver.current_url
            if "meet.google.com" not in current_url:
                logger.info("Redirected away from Meet - meeting ended.")
                return True
        except Exception:
            pass

    if platform == "zoom":
        current_url = access.driver.current_url
        if "meeting/end" in current_url or "reason=ended" in current_url:
            return True
        try:
            dialog = access.driver.find_element(By.CSS_SELECTOR, ".zm-modal-body-title")
            if "ended" in dialog.text.lower():
                return True
        except NoSuchElementException:
            pass

    if platform == "teams":
        try:
            page_src = access.driver.page_source
            for phrase in TEAMS_END_PHRASES:
                if phrase in page_src:
                    logger.info("[Teams] Meeting ended - found phrase: '%s'", phrase)
                    return True
        except Exception:
            pass

    if platform == "zoom_sdk":
        try:
            page_src = access.driver.page_source
            if "Meeting ended" in page_src:
                return True
        except Exception:
            pass

    if end_xpath:
        try:
            access.driver.find_element(By.XPATH, end_xpath)
            return True
        except NoSuchElementException:
            pass

    return False


def is_alone_in_meeting(access: "MeetingAccess", platform_sel: dict[str, Any]) -> bool:
    """Return True if the agent appears to be the only participant."""
    platform = access.platform_key
    if platform not in ("google_meet", "teams"):
        return False

    if platform == "teams":
        try:
            page_lower = access.driver.page_source.lower()
            if any(indicator in page_lower for indicator in LOBBY_PHRASES):
                logger.debug("[Teams] Bot is still in lobby - not checking alone status.")
                return False
        except Exception:
            pass

    alone_patterns = ALONE_PATTERNS.get(platform, [])

    try:
        page_src = access.driver.page_source
        for pattern in alone_patterns:
            if pattern in page_src:
                logger.info("Alone detected via page_source: found '%s'.", pattern)
                return True
    except Exception as exc:
        logger.debug("page_source check failed: %s", exc)

    try:
        result = access.driver.execute_script(
            """
            var patterns = arguments[0];
            var debug = {};

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

            var bodyText = document.body.textContent || '';
            debug.textLength = bodyText.length;
            debug.textSnippet = bodyText.substring(0, 200);

            for (var j = 0; j < patterns.length; j++) {
                if (bodyText.indexOf(patterns[j]) !== -1) {
                    return {alone: true, reason: 'textContent', debug: debug};
                }
            }

            var tiles = document.querySelectorAll(
                '[data-participant-id], [data-requested-participant-id]'
            );
            debug.tileCount = tiles.length;

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
            alone_patterns,
        )

        if result:
            debug_info = result.get("debug", {})
            if result.get("alone"):
                logger.info(
                    "Alone detected via JS (reason=%s) | tiles=%s visible=%s alerts=%s",
                    result.get("reason"),
                    debug_info.get("tileCount"),
                    debug_info.get("visibleTiles"),
                    debug_info.get("alertCount"),
                )
                return True

            logger.debug(
                "Not alone | tiles=%s visible=%s alerts=%s alertTexts=%s textSnippet='%s'",
                debug_info.get("tileCount"),
                debug_info.get("visibleTiles"),
                debug_info.get("alertCount"),
                debug_info.get("alertTexts"),
                str(debug_info.get("textSnippet", ""))[:100],
            )
    except Exception as exc:
        logger.warning("JS alone-detection error: %s", exc)

    return False


def click_leave_button(access: "MeetingAccess") -> None:
    """Attempt to click the platform leave button."""
    platform = access.platform_key

    if platform == "google_meet":
        sel = access.selectors.get("google_meet", {})
        leave_strategies = [
            (By.CSS_SELECTOR, sel.get("leave_call_button", "")),
            (By.XPATH, "//button[@aria-label='Leave call']"),
            (By.XPATH, "//button[contains(@aria-label, 'Leave')]"),
            (By.CSS_SELECTOR, "button[jsname='CQylAd']"),
            (By.CSS_SELECTOR, "[data-tooltip='Leave call']"),
        ]
        if not access._try_click_strategies(leave_strategies, timeout=3):
            logger.warning("[Google Meet] Could not find leave button.")

    elif platform == "teams":
        sel = access.selectors.get("teams", {})
        try:
            btn = access._wait(3).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, sel.get("leave_call_button", "[data-tid='leave-call-btn']"))
                )
            )
            btn.click()
            logger.info("[Teams] Clicked leave button.")
        except (TimeoutException, NoSuchElementException):
            logger.warning("[Teams] Could not find leave button.")

