"""Chrome WebDriver construction helpers."""

from __future__ import annotations

from typing import Any

from selenium.webdriver.chrome.options import Options


def build_chrome_options(*, headless: bool = False) -> Options:
    """Build Chrome options used by the meeting automation bot."""
    options = Options()
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--use-fake-device-for-media-stream")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_experimental_option(
        "prefs",
        {
            "protocol_handler": {
                "excluded_schemes": {
                    "zoommtg": True,
                    "zoomus": True,
                    "zoom": True,
                }
            }
        },
    )
    if headless:
        options.add_argument("--headless=new")
    return options


def create_chrome_driver(
    *,
    headless: bool,
    webdriver_module: Any,
    service_cls: Any,
    manager_cls: Any,
) -> Any:
    """Create Chrome WebDriver using injected facade-level dependencies."""
    options = build_chrome_options(headless=headless)
    service = service_cls(manager_cls().install())
    return webdriver_module.Chrome(service=service, options=options)

