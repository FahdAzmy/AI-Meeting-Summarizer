"""
modules/stt_errors.py
---------------------
Custom exception structs (TR-001 through TR-005) for the Transcription Module.

Each exception maps one-to-one with a specific failure mode documented in the
data-model, allowing the orchestrator to make deterministic routing decisions
without catching broad base exceptions.

Exceptions
----------
  TR-001  STTProviderError       — Generic HTTP 5xx or unclassified SDK error.
  TR-002  STTTimeoutError        — HTTP 408; triggers exponential backoff retry.
  TR-003  STTRateLimitError      — HTTP 429; triggers provider fallback switch.
  TR-004  AudioTooLargeError     — File exceeds 25 MB upload limit.
  TR-005  NormalisationError     — Raw API response violates the TranscriptResult schema.
"""


class STTProviderError(Exception):
    """TR-001: General STT provider failure (HTTP 5xx or unknown SDK exception).

    Raised when an API call fails with an unrecoverable server error and no
    specific retry or fallback strategy is defined for the status code.
    """

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"[TR-001] STT provider '{provider}' error: {message}")


class STTTimeoutError(Exception):
    """TR-002: STT request timed out (HTTP 408).

    Raised after all exponential-backoff retry attempts are exhausted.
    The caller may choose to fall back to a secondary provider.
    """

    def __init__(self, provider: str, attempts: int) -> None:
        self.provider = provider
        self.attempts = attempts
        super().__init__(
            f"[TR-002] STT provider '{provider}' timed out after {attempts} attempt(s)."
        )


class STTRateLimitError(Exception):
    """TR-003: STT request rate-limited (HTTP 429).

    Raised when the current provider returns 429.  The transcription router
    catches this and switches to the next configured provider.
    """

    def __init__(self, provider: str) -> None:
        self.provider = provider
        super().__init__(
            f"[TR-003] STT provider '{provider}' rate-limit exceeded (HTTP 429)."
        )


class AudioTooLargeError(Exception):
    """TR-004: Audio file exceeds the maximum upload size (25 MB).

    Raised by the file-size guard at the top of ``Transcription.transcribe()``
    before any network I/O is attempted, avoiding wasted upload bandwidth.
    """

    MAX_BYTES: int = 25 * 1024 * 1024  # 25 MB

    def __init__(self, path: str, size_bytes: int) -> None:
        self.path = path
        self.size_bytes = size_bytes
        super().__init__(
            f"[TR-004] Audio file '{path}' is {size_bytes:,} bytes "
            f"(limit: {self.MAX_BYTES:,} bytes / 25 MB)."
        )


class NormalisationError(Exception):
    """TR-005: Raw API response could not be mapped to the TranscriptResult schema.

    Raised inside ``Transcription._normalise()`` when expected keys are missing
    or carry incompatible types, preventing corrupt data from reaching downstream
    LLM summarisers.
    """

    def __init__(self, provider: str, reason: str) -> None:
        self.provider = provider
        super().__init__(
            f"[TR-005] Failed to normalise response from '{provider}': {reason}"
        )
