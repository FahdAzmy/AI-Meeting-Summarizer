"""
Meeting Access Module – Custom Exceptions
Error codes MA-001 through MA-004 as defined in the data-model spec.
"""


class MeetingJoinError(Exception):
    """MA-001: All retry_limit attempts exhausted hitting TimeoutException or NoSuchElementException."""

    code = "MA-001"

    def __init__(self, platform: str, attempt: int, cause: Exception | None = None):
        self.platform = platform
        self.attempt = attempt
        self.cause = cause
        super().__init__(
            f"[{self.code}] Failed to join {platform!r} after {attempt} attempt(s). "
            f"Cause: {cause!r}"
        )


class PlatformNotSupported(Exception):
    """MA-002: URL does not match any supported platform regex pattern."""

    code = "MA-002"

    def __init__(self, url: str):
        self.url = url
        super().__init__(
            f"[{self.code}] Unsupported or unrecognised meeting URL: {url!r}"
        )


class BrowserInitError(Exception):
    """MA-003: webdriver-manager failed to install or locate Chrome binaries."""

    code = "MA-003"

    def __init__(self, cause: Exception | None = None):
        self.cause = cause
        super().__init__(
            f"[{self.code}] Browser could not be initialised. Cause: {cause!r}"
        )


class WaitingRoomTimeout(Exception):
    """MA-004: Zoom waiting room visible beyond the hard timeout limit."""

    code = "MA-004"

    def __init__(self, timeout_seconds: int = 300):
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"[{self.code}] Waiting room persisted beyond {timeout_seconds}s timeout."
        )
