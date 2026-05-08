"""Microsoft Teams join strategy."""

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

TEAMS_SELECT_COMPUTER_AUDIO_SCRIPT = """
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

TEAMS_MIC_FALLBACK_SCRIPT = """
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

TEAMS_CAMERA_FALLBACK_SCRIPT = """
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

TEAMS_NAME_FALLBACK_SCRIPT = """
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
"""

TEAMS_JOIN_FALLBACK_SCRIPT = """
var btns = document.querySelectorAll('button');
for (var i = 0; i < btns.length; i++) {
    var t = (btns[i].innerText ||
             btns[i].textContent || '').trim();
    if (t === 'Join now' || t === 'Join Now') {
        btns[i].click(); return;
    }
}
"""


class TeamsStrategy:
    def __init__(self, access: "MeetingAccess") -> None:
        self.access = access

    def join(self, link: str) -> None:
        bot = self.access
        sel = bot.selectors.get("teams", {})
        is_live_url = "teams.live.com" in link

        for attempt in range(1, bot.retry_limit + 1):
            bot.current_attempt = attempt
            try:
                nav_link = bot._teams_web_url(link)
                logger.info("[Teams] Attempt %d/%d - navigating to %s", attempt, bot.retry_limit, nav_link)
                bot.driver.get(nav_link)

                wait = bot._wait(25)

                if is_live_url:
                    self._join_live_flow(wait, sel)
                else:
                    self._join_enterprise_flow(wait, sel)

                logger.info("[Teams] Joined successfully on attempt %d.", attempt)
                return

            except (TimeoutException, NoSuchElementException) as exc:
                logger.warning("[Teams] Attempt %d failed: %s", attempt, exc)
                if attempt < bot.retry_limit:
                    bot._sleep(10)

        raise MeetingJoinError(platform="teams", attempt=bot.retry_limit)

    def _join_live_flow(self, wait: object, sel: dict[str, str]) -> None:
        bot = self.access
        logger.info("[Teams] Waiting 20 s for pre-join SPA to render...")
        bot._sleep(20)

        try:
            bot.driver.execute_script(TEAMS_SELECT_COMPUTER_AUDIO_SCRIPT)
            logger.info("[Teams] Ensured 'Computer audio' is selected.")
        except Exception as exc:
            logger.warning("[Teams] Computer audio selection failed: %s", exc)

        bot._sleep(0.5)
        self._mute_microphone()
        bot._sleep(1)
        self._turn_camera_off()
        bot._sleep(1)
        self._enter_name(sel)
        bot._sleep(1)
        self._click_join_now(sel)

    def _mute_microphone(self) -> None:
        bot = self.access
        mic_muted = False
        for by, selector in [
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
                el = bot._wait(2).until(EC.presence_of_element_located((by, selector)))
                is_on = el.get_attribute("aria-checked") == "true" or el.get_attribute("checked") == "true"
                if is_on:
                    el.click()
                    logger.info("[Teams] Muted microphone via %s", selector)
                else:
                    logger.info("[Teams] Microphone already muted (%s)", selector)
                mic_muted = True
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not mic_muted:
            try:
                bot.driver.execute_script(TEAMS_MIC_FALLBACK_SCRIPT)
                logger.info("[Teams] Mic toggle clicked (JS fallback).")
            except Exception as exc:
                logger.warning("[Teams] JS mic toggle failed: %s", exc)

    def _turn_camera_off(self) -> None:
        bot = self.access
        camera_toggled = False
        for by, selector in [
            (By.CSS_SELECTOR, "[data-tid='toggle-video']"),
            (By.CSS_SELECTOR, "[data-tid='prejoin-video-toggle']"),
            (By.CSS_SELECTOR, "[aria-label*='camera' i][role='switch']"),
            (By.CSS_SELECTOR, "[aria-label*='camera' i][role='checkbox']"),
            (By.CSS_SELECTOR, "[aria-label*='video' i][role='switch']"),
            (By.CSS_SELECTOR, "[aria-label*='video' i][role='checkbox']"),
        ]:
            try:
                el = bot._wait(1).until(EC.presence_of_element_located((by, selector)))
                is_checked = el.get_attribute("aria-checked") == "true" or el.get_attribute("checked") == "true"
                if is_checked:
                    el.click()
                    logger.info("[Teams] Turned camera OFF via %s", selector)
                else:
                    logger.info("[Teams] Camera already OFF (%s)", selector)
                camera_toggled = True
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not camera_toggled:
            try:
                bot.driver.execute_script(TEAMS_CAMERA_FALLBACK_SCRIPT)
                logger.info("[Teams] Camera toggle clicked (JS fallback).")
            except Exception as exc:
                logger.warning("[Teams] Camera toggle JS failed: %s", exc)

    def _enter_name(self, sel: dict[str, str]) -> None:
        bot = self.access
        name_entered = False
        for by, selector in [
            (By.XPATH, "//input[@placeholder='Type your name']"),
            (By.XPATH, "//input[contains(@placeholder,'name')]"),
            (By.CSS_SELECTOR, "input[placeholder*='name']"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, sel.get("name_field", "")),
        ]:
            if not selector:
                continue
            try:
                field = bot._wait(5).until(EC.presence_of_element_located((by, selector)))
                field.clear()
                field.send_keys(bot.BOT_NAME)
                name_entered = True
                logger.info("[Teams] Entered name '%s' via %s='%s'.", bot.BOT_NAME, by, selector)
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not name_entered:
            try:
                bot.driver.execute_script(TEAMS_NAME_FALLBACK_SCRIPT, bot.BOT_NAME)
                name_entered = True
                logger.info("[Teams] Entered name via JS React fallback.")
            except Exception as exc:
                logger.warning("[Teams] JS name entry failed: %s", exc)

        if not name_entered:
            logger.warning("[Teams] Could not enter bot name - continuing.")

    def _click_join_now(self, sel: dict[str, str]) -> None:
        bot = self.access
        joined = False
        for by, selector in [
            (By.XPATH, "//button[normalize-space(.)='Join now']"),
            (By.XPATH, "//button[contains(.,'Join now')]"),
            (By.XPATH, "//button[contains(.,'Join Now')]"),
            (By.CSS_SELECTOR, "[data-tid='prejoin-join-button']"),
            (By.CSS_SELECTOR, sel.get("join_button", "")),
        ]:
            if not selector:
                continue
            try:
                btn = bot._wait(8).until(EC.element_to_be_clickable((by, selector)))
                btn.click()
                logger.info("[Teams] Clicked 'Join now' via %s='%s'.", by, selector)
                joined = True
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not joined:
            bot.driver.execute_script(TEAMS_JOIN_FALLBACK_SCRIPT)
            logger.info("[Teams] Clicked 'Join now' via JS last-resort.")

    def _join_enterprise_flow(self, wait: object, sel: dict[str, str]) -> None:
        bot = self.access
        use_browser = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, sel.get("use_browser_link", "a[data-tid='joinOnWeb']")))
        )
        use_browser.click()

        bot._safe_click(wait, sel.get("continue_without_audio", "[data-tid='prejoin-ok-cta']"), By.CSS_SELECTOR)
        bot._safe_click(wait, sel.get("mute_mic", "[data-tid='toggle-mute']"), By.CSS_SELECTOR)

        join_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, sel.get("join_button", "[data-tid='call-join-button']")))
        )
        join_btn.click()

