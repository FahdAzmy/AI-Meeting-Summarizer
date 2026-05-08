"""Constants used by meeting access flows."""

from __future__ import annotations

from pathlib import Path

from .types import Platform

SELECTORS_PATH = Path(__file__).parent.parent.parent / "config" / "selectors.json"

LOBBY_PHRASES = [
    "someone will let you in",
    "waiting to be let in",
    "waiting to be admitted",
    "let you in shortly",
    "please wait",
]

LOBBY_END_PHRASES = [
    "the meeting has ended",
    "you have left the meeting",
    "meeting has been cancelled",
    "enjoy your call?",
]

TEAMS_END_PHRASES = [
    "The meeting has ended",
    "You have left the meeting",
    "Enjoy your call?",
    "Rejoin the call",
    "Did you leave by mistake?",
    "Your meeting has expired",
]

ALONE_PATTERNS: dict[str, list[str]] = {
    Platform.GOOGLE_MEET.value: [
        "No one else is in this meeting",
        "You're the only one here",
        "You are the only one here",
        "Just you",
    ],
    Platform.TEAMS.value: [
        "Waiting for others to join",
        "Waiting for people to join",
        "You're the only one in the meeting",
        "You are the only one in the meeting",
        "You're the only one here",
        "You are the only one here",
    ],
}

