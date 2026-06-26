"""Zoom web-client join strategy."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from modules.errors import MeetingJoinError, WaitingRoomTimeout

if TYPE_CHECKING:
    from modules.meeting_access import MeetingAccess

logger = logging.getLogger(__name__)

ZOOM_PREJOIN_SCRIPT = """
var botName = arguments[0];

// 1. Mute microphone - button whose text is exactly "Mute"
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
"""

ZOOM_JOIN_FALLBACK_SCRIPT = """
var btns = document.querySelectorAll('button');
for (var i = 0; i < btns.length; i++) {
    var t = (btns[i].innerText || btns[i].textContent || '').trim();
    if (t === 'Join') { btns[i].click(); break; }
}
"""


class ZoomStrategy:
    def __init__(self, access: "MeetingAccess") -> None:
        self.access = access

    def join(self, link: str) -> None:
        bot = self.access
        sel = bot.selectors.get("zoom", {})
        web_link = bot._zoom_web_client_url(link)

        for attempt in range(1, bot.retry_limit + 1):
            bot.current_attempt = attempt
            try:
                logger.info("[Zoom] Attempt %d/%d - navigating to web client: %s", attempt, bot.retry_limit, web_link)
                bot.driver.get(web_link)

                bot._sleep(5)
                bot.driver.execute_script(ZOOM_PREJOIN_SCRIPT, bot.BOT_NAME)
                logger.info("[Zoom] Muted mic and entered name '%s' via JS.", bot.BOT_NAME)

                bot._sleep(0.5)

                joined = False
                for by, selector in [
                    (By.XPATH, "//button[normalize-space(text())='Join']"),
                    (By.XPATH, "//button[.//span[normalize-space(text())='Join']]"),
                    (By.CSS_SELECTOR, sel.get("join_button", "")),
                ]:
                    if not selector:
                        continue
                    try:
                        join_btn = bot._wait(5).until(EC.element_to_be_clickable((by, selector)))
                        join_btn.click()
                        logger.info("[Zoom] Clicked Join via %s='%s'.", by, selector)
                        joined = True
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue

                if not joined:
                    bot.driver.execute_script(ZOOM_JOIN_FALLBACK_SCRIPT)
                    logger.info("[Zoom] Clicked Join via JS fallback.")

                wait = bot._wait(15)
                bot._handle_zoom_waiting_room(wait, sel)

                logger.info("[Zoom] Joined successfully on attempt %d.", attempt)
                return

            except WaitingRoomTimeout:
                raise
            except (TimeoutException, NoSuchElementException) as exc:
                logger.warning("[Zoom] Attempt %d failed: %s", attempt, exc)
                if attempt < bot.retry_limit:
                    bot._sleep(10)

        raise MeetingJoinError(platform="zoom", attempt=bot.retry_limit)

    def handle_waiting_room(self, wait: Any, sel: dict[str, Any]) -> None:
        """Poll for waiting room indicator and raise WaitingRoomTimeout if exceeded."""
        bot = self.access
        deadline = bot._now() + 300
        wr_xpath = sel.get("waiting_room_text", "//p[contains(text(), 'Please wait')]")
        while bot._now() < deadline:
            try:
                bot.driver.find_element(By.XPATH, wr_xpath)
                logger.debug("[Zoom] Still in waiting room...")
                bot._sleep(10)
            except NoSuchElementException:
                return
        raise WaitingRoomTimeout(timeout_seconds=300)

