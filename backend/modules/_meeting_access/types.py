"""Shared types for meeting access internals."""

from __future__ import annotations

from enum import Enum
from typing import TypedDict


class Platform(str, Enum):
    """Supported meeting platform identifiers."""

    GOOGLE_MEET = "google_meet"
    ZOOM = "zoom"
    TEAMS = "teams"
    ZOOM_SDK = "zoom_sdk"


class PlatformSelectors(TypedDict, total=False):
    """Selector keys loaded from config/selectors.json."""

    alone_banner_text: str
    ask_to_join_button: str
    continue_without_audio: str
    dismiss_dialog: str
    dont_use_audio: str
    end_screen: str
    end_text: str
    join_audio_button: str
    join_button: str
    join_now_button: str
    leave_call_button: str
    meeting_end_dialog: str
    meeting_end_text: str
    mute_cam: str
    mute_mic: str
    name_field: str
    participant_count: str
    use_browser_link: str
    waiting_room_indicator: str
    waiting_room_text: str


SelectorsConfig = dict[str, PlatformSelectors]
LocatorStrategy = tuple[str, str]

