"""Selector configuration loading."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .types import SelectorsConfig

logger = logging.getLogger(__name__)


def load_selectors(selectors_path: Path | str) -> SelectorsConfig:
    """Load selector configuration, preserving the legacy empty-config fallback."""
    try:
        return json.loads(Path(selectors_path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("selectors.json not found or invalid - using empty selectors. %s", exc)
        return {}

