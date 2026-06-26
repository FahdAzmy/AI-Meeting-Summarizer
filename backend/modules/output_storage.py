"""
modules/output_storage.py
-------------------------
Compatibility facade for the Output & Storage module.

The implementation lives under ``modules._output_storage`` so persistence,
email rendering, template loading, and SMTP delivery can evolve separately.
The public import path is intentionally preserved:

    from modules.output_storage import OutputStorage
"""

from __future__ import annotations

import aiosmtplib
from aiosmtplib import SMTPConnectError, SMTPException

from config.settings import Config
from modules._output_storage.constants import (
    PARTIAL_PATHS as _PARTIAL_PATHS,
    TEMPLATE_PATH as _TEMPLATE_PATH,
    TEMPLATES_DIR as _TEMPLATES_DIR,
    VALID_BACKENDS as _VALID_BACKENDS,
)
from modules._output_storage.service import OutputStorage as _OutputStorage
from modules._output_storage.templates import (
    load_partial as _load_partial,
    load_template as _load_template,
)
from modules.storage_errors import (
    DatabaseWriteError,
    EmailDeliveryError,
    InvalidBackendError,
)


class OutputStorage(_OutputStorage):
    """Compatibility subclass preserving the historical module patch surface."""

    def __init__(
        self,
        backend: str = "database",
        config: Config | None = None,
    ) -> None:
        super().__init__(backend=backend, config=config or Config())

__all__ = ["OutputStorage"]
