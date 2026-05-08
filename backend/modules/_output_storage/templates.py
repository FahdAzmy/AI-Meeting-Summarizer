"""Cached template loading for output-storage emails."""

from __future__ import annotations

import logging
from functools import lru_cache

from modules._output_storage.constants import PARTIAL_PATHS, TEMPLATE_PATH

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_template() -> str:
    """Return the main HTML email template, reading from disk once."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    logger.debug("[OS] Email template loaded from %s", TEMPLATE_PATH)
    return template


@lru_cache(maxsize=None)
def load_partial(name: str) -> str:
    """Return a cached HTML partial by registered partial key."""
    path = PARTIAL_PATHS[name]
    partial = path.read_text(encoding="utf-8")
    logger.debug("[OS] Partial '%s' loaded from %s", name, path)
    return partial
