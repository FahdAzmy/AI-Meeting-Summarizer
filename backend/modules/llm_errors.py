"""
modules/llm_errors.py
---------------------
Custom exception architecture for the Summarisation & Analysis Module.

Error Codes
-----------
  SM-001  LLMAPIError         – General HTTP 500 / API-level failure from the LLM provider.
  SM-002  LLMTimeoutError     – Generation exceeded the time boundary or the request stalled.
  SM-003  ParseError          – JSON Mode response did not match the expected schema.
  SM-004  EmptyTranscriptError– Transcript supplied was empty (0 bytes / no full_text).
"""


class LLMAPIError(Exception):
    """SM-001: General API-level fault when querying the LLM provider (e.g. HTTP 500)."""

    code = "SM-001"

    def __init__(self, message: str = "LLM API request failed.", cause: Exception | None = None):
        self.cause = cause
        super().__init__(f"[{self.code}] {message} Cause: {cause!r}")


class LLMTimeoutError(Exception):
    """SM-002: LLM generation exceeded the allowed time boundary or request stalled."""

    code = "SM-002"

    def __init__(self, timeout_seconds: int | None = None, cause: Exception | None = None):
        self.timeout_seconds = timeout_seconds
        self.cause = cause
        detail = f" (timeout={timeout_seconds}s)" if timeout_seconds is not None else ""
        super().__init__(
            f"[{self.code}] LLM request timed out{detail}. Cause: {cause!r}"
        )


class ParseError(Exception):
    """SM-003: JSON Mode parsing failed – response did not conform to the expected schema."""

    code = "SM-003"

    def __init__(self, message: str = "Failed to parse LLM JSON response.", cause: Exception | None = None):
        self.cause = cause
        super().__init__(f"[{self.code}] {message} Cause: {cause!r}")


class EmptyTranscriptError(Exception):
    """SM-004: Transcript supplied contained no text – fast-exit to avoid unnecessary API costs."""

    code = "SM-004"

    def __init__(self, message: str = "Transcript is empty and cannot be summarised."):
        super().__init__(f"[{self.code}] {message}")
