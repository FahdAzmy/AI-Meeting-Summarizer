"""
modules/storage_errors.py
--------------------------
Custom exception structs (OS-001, OS-003, OS-004) for the Output & Storage Module.

Each exception maps one-to-one with a specific failure mode documented in the
data-model, allowing the pipeline orchestrator to make deterministic routing
decisions and trigger the correct fallback strategy without catching broad base
exceptions.

Exceptions
----------
  OS-001  EmailDeliveryError    — Global SMTP failure or authentication blockade.
  OS-003  DatabaseWriteError    — MongoDB engine failure during ``await meeting.save()``.
  OS-004  InvalidBackendError   — Unconfigured or unrecognised ``backend`` value.
"""


class EmailDeliveryError(Exception):
    """OS-001: SMTP transport failure or authentication blockade.

    Raised when ``aiosmtplib`` raises an ``SMTPException`` that is not a
    per-recipient bounce.  A per-recipient bounce is captured separately and
    returned as a structured failure dict; this exception signals a *global*
    SMTP failure that aborts the entire send operation.

    Parameters
    ----------
    recipient:
        The target email address that triggered the failure, or ``"global"``
        when the failure occurred before any individual send attempt.
    cause:
        The underlying ``SMTPException`` (or other exception) that was caught.
    """

    code = "OS-001"

    def __init__(self, recipient: str, cause: Exception | None = None) -> None:
        self.recipient = recipient
        self.cause = cause
        super().__init__(
            f"[{self.code}] Email delivery failed for '{recipient}'. "
            f"Cause: {cause!r}"
        )


class DatabaseWriteError(Exception):
    """OS-003: MongoDB persistence failure during ``await meeting.save()``.

    Raised when the Beanie ODM (backed by the Motor async driver) raises any
    exception while committing a ``Meeting`` document.  Because persistent
    storage is the primary output of the pipeline, this is a hard failure that
    propagates as HTTP 500 to the caller.

    Parameters
    ----------
    meeting_id:
        The identifier of the ``Meeting`` document that failed to save.
    cause:
        The underlying Motor / Beanie exception that was caught.
    """

    code = "OS-003"

    def __init__(self, meeting_id: str, cause: Exception | None = None) -> None:
        self.meeting_id = meeting_id
        self.cause = cause
        super().__init__(
            f"[{self.code}] Database write failed for meeting '{meeting_id}'. "
            f"Cause: {cause!r}"
        )


class InvalidBackendError(Exception):
    """OS-004: Unrecognised or unconfigured ``backend`` routing value.

    Raised by the ``OutputStorage`` constructor (or the ``store()`` dispatcher)
    when the ``backend`` parameter does not match any known routing target
    (e.g. ``'database'``).  This prevents silent mis-routing due to typos or
    missing environment variables.

    Parameters
    ----------
    backend:
        The invalid backend string that was supplied.
    """

    code = "OS-004"

    VALID_BACKENDS: frozenset[str] = frozenset({"database"})

    def __init__(self, backend: str) -> None:
        self.backend = backend
        super().__init__(
            f"[{self.code}] Unrecognised backend '{backend}'. "
            f"Valid options: {sorted(self.VALID_BACKENDS)}"
        )
