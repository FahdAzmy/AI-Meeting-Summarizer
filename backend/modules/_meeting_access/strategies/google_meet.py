"""Google Meet join strategy."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from modules.errors import MeetingJoinError

if TYPE_CHECKING:
    from modules.meeting_access import MeetingAccess

logger = logging.getLogger(__name__)


class GoogleMeetStrategy:
    def __init__(self, access: "MeetingAccess") -> None:
        self.access = access

    def join(self, link: str) -> None:
        bot = self.access
        sel = bot.selectors.get("google_meet", {})

        for attempt in range(1, bot.retry_limit + 1):
            bot.current_attempt = attempt
            try:
                logger.info("[Google Meet] Attempt %d/%d - navigating to %s", attempt, bot.retry_limit, link)
                bot.driver.get(link)

                # ── Step 1: Wait for page to fully load ──────────────────
                # The Google Meet pre-join page can take a long time to
                # render all its elements. We wait up to 60s for either
                # the name field or a join button to appear, whichever
                # comes first. This ensures the page is ready before we
                # interact with anything.
                logger.info("[Google Meet] Waiting for pre-join page to fully load...")
                page_ready = False
                page_indicators = [
                    (By.XPATH, "//input[@placeholder='Your name']"),
                    (By.XPATH, "//input[@aria-label='Your name']"),
                    (By.CSS_SELECTOR, sel.get("name_field", "")),
                    (By.XPATH, "//button[contains(., 'Ask to join')]"),
                    (By.XPATH, "//button[contains(., 'Join now')]"),
                ]
                for by, selector in page_indicators:
                    if not selector:
                        continue
                    try:
                        bot._wait(60).until(EC.presence_of_element_located((by, selector)))
                        logger.info("[Google Meet] Page loaded — detected element via %s='%s'.", by, selector)
                        page_ready = True
                        break
                    except TimeoutException:
                        continue

                if not page_ready:
                    raise TimeoutException("Pre-join page did not load within 60 seconds.")

                # Small extra pause to let remaining UI elements render
                bot._sleep(2)

                # Dismiss any popup dialogs (cookie consent, etc.)
                wait = bot._wait(10)
                bot._safe_click(wait, sel.get("dismiss_dialog", ""), By.CSS_SELECTOR)

                # ── Step 2: Mute mic and camera FIRST ────────────────────
                logger.info("[Google Meet] Muting microphone and camera...")
                bot._safe_click(wait, sel.get("mute_mic", ""), By.CSS_SELECTOR)
                bot._sleep(0.5)
                bot._safe_click(wait, sel.get("mute_cam", ""), By.CSS_SELECTOR)
                bot._sleep(0.5)
                logger.info("[Google Meet] Mic and camera muted.")

                # ── Step 3: Enter bot name ───────────────────────────────
                name_entered = False
                name_strategies = [
                    (By.CSS_SELECTOR, sel.get("name_field", "")),
                    (By.XPATH, "//input[@placeholder='Your name']"),
                    (By.XPATH, "//input[@aria-label='Your name']"),
                    (By.XPATH, "//input[@type='text']"),
                    (By.CSS_SELECTOR, "input[type='text']"),
                ]
                for by, selector in name_strategies:
                    if not selector:
                        continue
                    try:
                        name_field = bot._wait(10).until(EC.presence_of_element_located((by, selector)))
                        name_field.clear()
                        name_field.send_keys(bot.BOT_NAME)
                        name_entered = True
                        logger.info("[Google Meet] Entered bot name via %s='%s'.", by, selector)
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue

                if not name_entered:
                    logger.debug("[Google Meet] No name field found - likely signed in.")

                bot._sleep(1)

                # ── Step 4: Click join button ────────────────────────────
                logger.info("[Google Meet] Looking for join button...")
                joined = False
                join_strategies = [
                    (By.XPATH, "//button[.//span[text()='Ask to join']]"),
                    (By.XPATH, "//button[contains(., 'Ask to join')]"),
                    (By.XPATH, "//button[.//span[text()='Join now']]"),
                    (By.XPATH, "//button[contains(., 'Join now')]"),
                    (By.CSS_SELECTOR, sel.get("ask_to_join_button", "")),
                    (By.CSS_SELECTOR, sel.get("join_now_button", "")),
                ]
                for by, selector in join_strategies:
                    if not selector:
                        continue
                    try:
                        join_btn = bot._wait(10).until(EC.element_to_be_clickable((by, selector)))
                        join_btn.click()
                        logger.info("[Google Meet] Clicked join via %s='%s' on attempt %d.", by, selector, attempt)
                        joined = True
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue

                if not joined:
                    raise TimeoutException("Neither 'Ask to join' nor 'Join now' button found.")

                logger.info("[Google Meet] Joined successfully on attempt %d.", attempt)
                return

            except (TimeoutException, NoSuchElementException) as exc:
                logger.warning("[Google Meet] Attempt %d failed: %s", attempt, exc)
                if attempt < bot.retry_limit:
                    bot._sleep(10)

        raise MeetingJoinError(platform="google_meet", attempt=bot.retry_limit)

