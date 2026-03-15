# Quickstart: Meeting Access Module

This guide provides developer instructions to run local implementations and test environments for the Selenium-based `meeting_access` module.

## Prerequisites

- Python `3.10+`
- Google Chrome installed on the host machine.
- (Optional but recommended) A virtual environment like `venv` or `conda`.

## Setup

1. **Navigate to the core project directory**
   ```bash
   cd project
   ```

2. **Install Python dependencies locally**
   Ensure `webdriver-manager` and `selenium` are loaded from requirements.
   ```bash
   pip install selenium webdriver-manager
   ```

3. **Initialize Configuration**
   Verify the `config/selectors.json` payload map exists. If not, generate a baseline version containing empty hashes for `google_meet` etc., so the JSON parser does not fail to boot.

## Running Tests (TDD)

Per the project constitution, mock your external calls! Selenium browsers should almost NEVER be spun up during standard unit testing runs to keep testing extremely fast.

- To execute mocked TDD tests (which will assert logic trees and `Exception` routing):
  ```bash
  pytest tests/unit/test_meeting_access.py
  ```

## Local Prototyping

To genuinely test the bot against a live room without triggering the entire pipeline:
```python
# test_live.py (Do not commit)
from modules.meeting_access import MeetingAccess

bot = MeetingAccess()
bot.join("https://meet.google.com/test-room")
bot.wait_until_end()
bot.leave()
```
Execute via `python test_live.py`.
