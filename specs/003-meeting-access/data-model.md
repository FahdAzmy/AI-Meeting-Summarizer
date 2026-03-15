# Data Model: Meeting Access Module

This file defines the primary objects, attributes, and custom error enums utilized within the `meeting_access.py` module context.

## 1. MeetingAccess (Class)

The primary stateful driver orchestrating the browser.

- **driver** (`selenium.webdriver.Chrome`) - The active browser instance.
- **detected_platform** (`str`) - Internally tracked platform ID targeting the active run (`"google_meet"`, `"zoom"`, `"teams"`).
- **retry_limit** (`int`) - Hardcoded or initialized upper bounds (e.g. 3).
- **current_attempt** (`int`) - State tracker for failure notifications.

## 2. Exceptions (Custom Error Structs)

To standardize pipeline abortion and the resulting error-payload outputs. Inherits from Pythons base `Exception`.

- `MeetingJoinError` (`MA-001`): Tripped when all `retry_limit` attempts exhaust hitting `TimeoutException` or `NoSuchElementException`.
- `PlatformNotSupported` (`MA-002`): Tripped instantly during `_detect_platform()` if regex parsing fails.
- `BrowserInitError` (`MA-003`): Tripped if `webdriver-manager` fails to install or find Chrome binaries.
- `WaitingRoomTimeout` (`MA-004`): Tripped if bot detects a Zoom "waiting room" element, but it remains visible past a hard limit (e.g. 300 seconds).

## 3. Selector Configuration Payload

Ingested directly from `config/selectors.json`.

```json
{
  "google_meet": {
    "join_button": "css selector string",
    "mute_mic": "css selector string",
    "end_screen": "css selector string"
  },
  "zoom": { ... },
  "teams": { ... }
}
```
