# Phase 0: Outline & Technical Research

## Browser Automation Tooling

**Decision**: Selenium WebDriver alongside `webdriver-manager`.
**Rationale**: Native Selenium provides the most robust set of low-level commands required to interact with deeply nested and constantly changing DOM structures on platforms like Google Meet and Zoom. `webdriver-manager` ensures that matching `chromedriver` versions are automatically downloaded independently of the host machine's manual browser version management.
**Alternatives considered**: Playwright (Python). Playwright is faster and uses WebSocket communication, however, Selenium often triggers fewer bot-detection alarms across highly secured meeting platforms right out of the box when combined with `--disable-blink-features=AutomationControlled` arguments. 

## Headless mode vs Display mode

**Decision**: Run Chrome with fake UI flags (`--use-fake-ui-for-media-stream`, `--use-fake-device-for-media-stream`) and consider `Xvfb` proxying on Linux host deployments to run "headless-like" visual rendering if pure Headless triggers bot blocks.
**Rationale**: Virtual meeting platforms aggressively block or fail to render WebRTC components in strict `--headless` environments. Injecting fake audio/video streams satisfies the browser's hardware permission requests automatically.
**Alternatives considered**: Traditional headless mode. Rejected due to historic unreliability when running WebRTC integrations for meeting audio intercepts.

## Dynamic CSS Selector Management

**Decision**: Outsource element identifiers to an external JSON configuration (`config/selectors.json`).
**Rationale**: Microsoft Teams, Zoom, and Google are notorious for performing A/B tests or deploying DOM updates that randomly change button IDs or class names. Hardcoding these strings directly into Python control flows requires application rebuilds or redeploys to fix. Decoupling them allows hot-reloading selector files on the fly.
**Alternatives considered**: Hardcoded class constants. Rejected for maintainability.

## Retry and Exception Polling Strategy

**Decision**: Selenium `WebDriverWait` explicit waits combined with a 3-attempt outer retry loop encompassing 10-second delays.
**Rationale**: The bot frequently outpaces the loading of dynamic single-page applications. Explicit waits (`EC.presence_of_element_located`) ensure no actions trigger prematurely. Outer loops handle broader network disconnects or intermittent DOM failures.
