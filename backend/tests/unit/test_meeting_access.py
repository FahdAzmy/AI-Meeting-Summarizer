"""
Unit tests for MeetingAccess module.
All Selenium interactions are mocked via unittest.mock – no real browser is launched.

Coverage map:
  T005  – Base fixture (mock Chrome) + import sanity
  T006  – _detect_platform valid & invalid URLs
  T007  – __init__ injects fake-media Chrome flags
  T008  – Google Meet join interaction sequence
  T009  – Zoom join display-name text-sending sequence
  T010  – MS Teams join iframe / button sequence
  T018  – wait_until_end polling exits when end-screen found
  T019  – leave() calls driver.quit()
  T024  – NoSuchElementException fires retry loop (3 attempts)
  T025  – MeetingJoinError raised after retries exhausted
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, call, patch

import pytest

from modules.errors import (
    BrowserInitError,
    MeetingJoinError,
    PlatformNotSupported,
    WaitingRoomTimeout,
)

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

SELECTORS_PATH = Path(__file__).parent.parent.parent / "config" / "selectors.json"

GOOGLE_MEET_URL = "https://meet.google.com/abc-defg-hij"
ZOOM_URL = "https://us02web.zoom.us/j/1234567890"
TEAMS_URL = (
    "https://teams.microsoft.com/l/meetup-join/19%3ameeting_abc/0?context=%7b%7d"
)
INVALID_URL = "https://example.com/meeting?token=xyz"


def _make_mock_driver() -> MagicMock:
    """Return a fully-mocked Chrome WebDriver."""
    driver = MagicMock()
    driver.current_url = GOOGLE_MEET_URL
    return driver


# ──────────────────────────────────────────────────────────────
# T005 – Base fixture: mock Chrome so no browser opens
# ──────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_chrome(tmp_path):
    """Patch webdriver.Chrome and ChromeDriverManager globally so no browser spawns."""
    with (
        patch("modules.meeting_access.webdriver.Chrome") as mock_cls,
        patch("modules.meeting_access.ChromeDriverManager") as mock_mgr,
        patch("modules.meeting_access.Service"),
    ):
        mock_mgr.return_value.install.return_value = "/fake/chromedriver"
        mock_cls.return_value = _make_mock_driver()
        yield mock_cls, mock_cls.return_value


@pytest.fixture()
def bot(mock_chrome, tmp_path):
    """Return a fully-instantiated MeetingAccess with a mocked driver."""
    from modules.meeting_access import MeetingAccess

    instance = MeetingAccess(selectors_path=SELECTORS_PATH, retry_limit=3)
    return instance


# ──────────────────────────────────────────────────────────────
# T006 – _detect_platform: valid and invalid URLs
# ──────────────────────────────────────────────────────────────


class TestDetectPlatform:
    def test_google_meet_url_detected(self):
        from modules.meeting_access import MeetingAccess

        assert MeetingAccess._detect_platform(GOOGLE_MEET_URL) == "google_meet"

    def test_zoom_url_detected(self):
        from modules.meeting_access import MeetingAccess

        assert MeetingAccess._detect_platform(ZOOM_URL) == "zoom"

    def test_teams_url_detected(self):
        from modules.meeting_access import MeetingAccess

        assert MeetingAccess._detect_platform(TEAMS_URL) == "teams"

    def test_invalid_url_raises_platform_not_supported(self):
        from modules.meeting_access import MeetingAccess

        with pytest.raises(PlatformNotSupported) as exc_info:
            MeetingAccess._detect_platform(INVALID_URL)
        assert exc_info.value.url == INVALID_URL
        assert "MA-002" in str(exc_info.value)

    def test_empty_string_raises_platform_not_supported(self):
        from modules.meeting_access import MeetingAccess

        with pytest.raises(PlatformNotSupported):
            MeetingAccess._detect_platform("")

    def test_meet_url_missing_room_code_raises(self):
        from modules.meeting_access import MeetingAccess

        with pytest.raises(PlatformNotSupported):
            MeetingAccess._detect_platform("https://meet.google.com/")


# ──────────────────────────────────────────────────────────────
# T007 – __init__: Chrome flags are injected
# ──────────────────────────────────────────────────────────────


class TestInit:
    def test_fake_ui_flag_injected(self, mock_chrome):
        """Chrome must be started with --use-fake-ui-for-media-stream."""
        from modules.meeting_access import MeetingAccess

        MeetingAccess(selectors_path=SELECTORS_PATH)
        init_options = mock_chrome[0].call_args[1]["options"]
        args = init_options.arguments
        assert "--use-fake-ui-for-media-stream" in args

    def test_fake_device_flag_injected(self, mock_chrome):
        """Chrome must be started with --use-fake-device-for-media-stream."""
        from modules.meeting_access import MeetingAccess

        MeetingAccess(selectors_path=SELECTORS_PATH)
        init_options = mock_chrome[0].call_args[1]["options"]
        args = init_options.arguments
        assert "--use-fake-device-for-media-stream" in args

    def test_automation_controlled_disabled(self, mock_chrome):
        from modules.meeting_access import MeetingAccess

        MeetingAccess(selectors_path=SELECTORS_PATH)
        init_options = mock_chrome[0].call_args[1]["options"]
        assert "--disable-blink-features=AutomationControlled" in init_options.arguments

    def test_browser_init_error_raised_on_webdriver_failure(self):
        """If Chrome raises, BrowserInitError should be propagated."""
        with (
            patch("modules.meeting_access.webdriver.Chrome", side_effect=RuntimeError("driver crash")),
            patch("modules.meeting_access.ChromeDriverManager"),
            patch("modules.meeting_access.Service"),
        ):
            from modules.meeting_access import MeetingAccess

            with pytest.raises(BrowserInitError) as exc_info:
                MeetingAccess(selectors_path=SELECTORS_PATH)
            assert "MA-003" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────
# T008 – Google Meet join interaction sequence
# ──────────────────────────────────────────────────────────────


class TestJoinGoogleMeet:
    def test_navigates_to_url(self, bot):
        """driver.get() must be called with the meeting URL."""
        with patch("modules.meeting_access.WebDriverWait") as mock_wait:
            wait_instance = MagicMock()
            mock_wait.return_value = wait_instance
            wait_instance.until.return_value = MagicMock()

            bot.join(GOOGLE_MEET_URL)

        bot.driver.get.assert_called_with(GOOGLE_MEET_URL)

    def test_detected_platform_set_to_google_meet(self, bot):
        with patch("modules.meeting_access.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = MagicMock()
            bot.join(GOOGLE_MEET_URL)
        assert bot.detected_platform == "google_meet"

    def test_join_button_clicked(self, bot):
        """The 'Join now' button element must be clicked."""
        mock_btn = MagicMock()
        with patch("modules.meeting_access.WebDriverWait") as mock_wait:
            wait_instance = MagicMock()
            mock_wait.return_value = wait_instance
            wait_instance.until.return_value = mock_btn

            bot.join(GOOGLE_MEET_URL)

        assert mock_btn.click.called


# ──────────────────────────────────────────────────────────────
# T009 – Zoom join: display name text-sending sequence
# ──────────────────────────────────────────────────────────────


class TestJoinZoom:
    def test_display_name_sent_to_name_field(self, bot):
        """Bot must type its name in the Zoom input field."""
        name_el = MagicMock()
        join_btn = MagicMock()

        with (
            patch("modules.meeting_access.WebDriverWait") as mock_wait,
            patch.object(bot, "_handle_zoom_waiting_room"),
        ):
            wait_instance = MagicMock()
            mock_wait.return_value = wait_instance
            wait_instance.until.side_effect = [name_el, join_btn]

            bot.join(ZOOM_URL)

        name_el.send_keys.assert_called_once_with("AI Meeting Assistant")

    def test_join_button_clicked_after_name(self, bot):
        name_el = MagicMock()
        join_btn = MagicMock()

        with (
            patch("modules.meeting_access.WebDriverWait") as mock_wait,
            patch.object(bot, "_handle_zoom_waiting_room"),
        ):
            wait_instance = MagicMock()
            mock_wait.return_value = wait_instance
            wait_instance.until.side_effect = [name_el, join_btn]

            bot.join(ZOOM_URL)

        join_btn.click.assert_called_once()

    def test_detected_platform_set_to_zoom(self, bot):
        with (
            patch("modules.meeting_access.WebDriverWait") as mock_wait,
            patch.object(bot, "_handle_zoom_waiting_room"),
        ):
            mock_wait.return_value.until.return_value = MagicMock()
            bot.join(ZOOM_URL)
        assert bot.detected_platform == "zoom"


# ──────────────────────────────────────────────────────────────
# T010 – MS Teams join: iframe bypass / button interactions
# ──────────────────────────────────────────────────────────────


class TestJoinTeams:
    def test_navigates_to_teams_url(self, bot):
        with patch("modules.meeting_access.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = MagicMock()
            bot.join(TEAMS_URL)
        bot.driver.get.assert_called_with(TEAMS_URL)

    def test_detected_platform_set_to_teams(self, bot):
        with patch("modules.meeting_access.WebDriverWait") as mock_wait:
            mock_wait.return_value.until.return_value = MagicMock()
            bot.join(TEAMS_URL)
        assert bot.detected_platform == "teams"

    def test_use_browser_link_clicked(self, bot):
        """Bot must click the 'use browser' anchor to bypass app prompt."""
        browser_link = MagicMock()
        join_btn = MagicMock()

        with patch("modules.meeting_access.WebDriverWait") as mock_wait:
            wait_instance = MagicMock()
            mock_wait.return_value = wait_instance
            # _join_teams makes 4 wait.until() calls:
            #   1. use_browser_link (explicit)
            #   2. continue_without_audio (_safe_click)
            #   3. mute_mic (_safe_click)
            #   4. join_button (explicit)
            wait_instance.until.side_effect = [browser_link, MagicMock(), MagicMock(), join_btn]

            bot.join(TEAMS_URL)

        browser_link.click.assert_called_once()


# ──────────────────────────────────────────────────────────────
# T018 – wait_until_end: polling exits when end element found
# ──────────────────────────────────────────────────────────────


class TestWaitUntilEnd:
    def test_exits_when_meeting_ended_element_found(self, bot):
        bot.detected_platform = "google_meet"

        with patch.object(bot, "_meeting_has_ended", side_effect=[False, False, True]):
            with patch("modules.meeting_access.time.sleep"):
                bot.wait_until_end(poll_interval=1)

        # Method should return without raising

    def test_polls_multiple_times_before_exit(self, bot):
        bot.detected_platform = "google_meet"
        responses = [False] * 4 + [True]

        with patch.object(bot, "_meeting_has_ended", side_effect=responses) as mock_end:
            with patch("modules.meeting_access.time.sleep"):
                bot.wait_until_end(poll_interval=1)

        assert mock_end.call_count == 5


# ──────────────────────────────────────────────────────────────
# T019 – leave(): calls driver.quit()
# ──────────────────────────────────────────────────────────────


class TestLeave:
    def test_driver_quit_called(self, bot):
        bot.leave()
        bot.driver.quit.assert_called_once()

    def test_leave_tolerates_quit_exception(self, bot):
        """leave() should not propagate errors from driver.quit()."""
        bot.driver.quit.side_effect = RuntimeError("already closed")
        bot.leave()  # Should not raise


# ──────────────────────────────────────────────────────────────
# T024 – NoSuchElementException fires retry loop (3 attempts)
# ──────────────────────────────────────────────────────────────


class TestRetryLoop:
    def test_google_meet_retries_three_times_on_failure(self, bot):
        """join() must retry exactly retry_limit times before giving up."""
        from selenium.common.exceptions import NoSuchElementException

        with (
            patch("modules.meeting_access.WebDriverWait") as mock_wait,
            patch("modules.meeting_access.time.sleep"),
        ):
            mock_wait.return_value.until.side_effect = NoSuchElementException("gone")

            with pytest.raises(MeetingJoinError):
                bot.join(GOOGLE_MEET_URL)

        # driver.get called once per attempt (3 total)
        assert bot.driver.get.call_count == bot.retry_limit

    def test_zoom_retries_three_times_on_failure(self, bot):
        from selenium.common.exceptions import TimeoutException

        with (
            patch("modules.meeting_access.WebDriverWait") as mock_wait,
            patch("modules.meeting_access.time.sleep"),
        ):
            mock_wait.return_value.until.side_effect = TimeoutException()

            with pytest.raises(MeetingJoinError):
                bot.join(ZOOM_URL)

        assert bot.driver.get.call_count == bot.retry_limit

    def test_teams_retries_three_times_on_failure(self, bot):
        from selenium.common.exceptions import TimeoutException

        with (
            patch("modules.meeting_access.WebDriverWait") as mock_wait,
            patch("modules.meeting_access.time.sleep"),
        ):
            mock_wait.return_value.until.side_effect = TimeoutException()

            with pytest.raises(MeetingJoinError):
                bot.join(TEAMS_URL)

        assert bot.driver.get.call_count == bot.retry_limit


# ──────────────────────────────────────────────────────────────
# T025 – MeetingJoinError raised after retries exhausted
# ──────────────────────────────────────────────────────────────


class TestMeetingJoinError:
    def test_error_code_is_ma001(self, bot):
        from selenium.common.exceptions import NoSuchElementException

        with (
            patch("modules.meeting_access.WebDriverWait") as mock_wait,
            patch("modules.meeting_access.time.sleep"),
        ):
            mock_wait.return_value.until.side_effect = NoSuchElementException("gone")

            with pytest.raises(MeetingJoinError) as exc_info:
                bot.join(GOOGLE_MEET_URL)

        assert exc_info.value.code == "MA-001"
        assert "MA-001" in str(exc_info.value)

    def test_error_contains_platform_name(self, bot):
        from selenium.common.exceptions import NoSuchElementException

        with (
            patch("modules.meeting_access.WebDriverWait") as mock_wait,
            patch("modules.meeting_access.time.sleep"),
        ):
            mock_wait.return_value.until.side_effect = NoSuchElementException("gone")

            with pytest.raises(MeetingJoinError) as exc_info:
                bot.join(GOOGLE_MEET_URL)

        assert "google_meet" in str(exc_info.value)

    def test_platform_not_supported_raised_before_driver_instantiation(self, bot):
        """PlatformNotSupported must fire immediately, before any webdriver action."""
        with pytest.raises(PlatformNotSupported):
            bot.join(INVALID_URL)

        # driver.get should never be called for an unsupported URL
        bot.driver.get.assert_not_called()
