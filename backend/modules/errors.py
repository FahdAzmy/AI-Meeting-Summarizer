"""
Shared Custom Exceptions for the AI Meeting Summarizer pipeline.

Meeting Access Module : Error codes MA-001 through MA-004
Audio Capture Module  : Error codes AC-001 through AC-005
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


# ---------------------------------------------------------------------------
# Audio Capture Module – AC-001 through AC-005
# ---------------------------------------------------------------------------

class OBSConnectionError(Exception):
    """AC-001: Socket timeout caused by bad credentials or unreachable OBS port."""

    code = "AC-001"

    def __init__(self, host: str, port: int, cause: Exception | None = None):
        self.host = host
        self.port = port
        self.cause = cause
        super().__init__(
            f"[{self.code}] Cannot connect to OBS at {host}:{port}. Cause: {cause!r}"
        )


class OBSNotRunning(Exception):
    """AC-002: OBS Studio is not running or the WebSocket server is disabled."""

    code = "AC-002"

    def __init__(self, host: str = "localhost", port: int = 4455):
        self.host = host
        self.port = port
        super().__init__(
            f"[{self.code}] OBS Studio does not appear to be running at {host}:{port}."
        )


class RecordingStartError(Exception):
    """AC-003: OBS returned a failure response upon start_record()."""

    code = "AC-003"

    def __init__(self, cause: Exception | None = None):
        self.cause = cause
        super().__init__(
            f"[{self.code}] OBS refused to start recording. Cause: {cause!r}"
        )


class RecordingStopError(Exception):
    """AC-004: OBS returned a failure response upon stop_record()."""

    code = "AC-004"

    def __init__(self, cause: Exception | None = None):
        self.cause = cause
        super().__init__(
            f"[{self.code}] OBS refused to stop recording. Cause: {cause!r}"
        )


class EmptyRecordingError(Exception):
    """AC-005: The saved audio file is 0 bytes or the path is unresolvable."""

    code = "AC-005"

    def __init__(self, path: str):
        self.path = path
        super().__init__(
            f"[{self.code}] Recording at {path!r} is empty or does not exist."
        )
