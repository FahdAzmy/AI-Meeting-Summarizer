"""Reusable Selenium interaction helpers."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from .types import LocatorStrategy


def try_click_strategies(
    *,
    wait_factory: Callable[[int], Any],
    strategies: list[LocatorStrategy],
    timeout: int = 5,
    logger: logging.Logger,
) -> bool:
    """Click the first available element from a list of locator strategies."""
    for by, selector in strategies:
        if not selector:
            continue
        try:
            btn = wait_factory(timeout).until(EC.element_to_be_clickable((by, selector)))
            btn.click()
            logger.info("Clicked element via %s='%s'.", by, selector)
            return True
        except (TimeoutException, NoSuchElementException) as exc:
            logger.debug("Click strategy failed for %s='%s': %s", by, selector, exc)
    return False


def safe_click(wait: Any, selector: str, by: str, *, logger: logging.Logger) -> None:
    """Click an element if present; silently skip if absent."""
    if not selector:
        return
    try:
        el = wait.until(EC.element_to_be_clickable((by, selector)))
        el.click()
    except (TimeoutException, NoSuchElementException) as exc:
        logger.debug("Optional click skipped for %s='%s': %s", by, selector, exc)

