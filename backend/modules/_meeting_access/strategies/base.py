"""Base strategy protocol."""

from __future__ import annotations

from typing import Protocol


class MeetingStrategy(Protocol):
    """Minimal interface for platform join strategies."""

    def join(self, link: str) -> None:
        """Join a meeting link."""

