# Quickstart: Output & Storage Module

This guide provides developer instructions to run local implementations and test environments for the `output_storage.py` backend pipeline architecture.

## Prerequisites

- Python `3.10+`
- Local or Cloud mapping accessing **MongoDB** structures cleanly.
- Preconfigured SMTP endpoint (e.g. standard local Gmail passwords).
- Standard developer `credentials.json` mapped securely for Google service account bindings if modifying the Sheets mapping logic.

## Setup Python

1. **Navigate to the core project directory**
   ```bash
   cd project
   ```

2. **Install Python dependencies**
   ```bash
   pip install motor beanie aiosmtplib gspread pandas pytest-asyncio
   ```

3. **Configure the Environment Maps**
   The application natively injects variables controlling destination vectors natively mapping inside the local `.env` structure securely targeted cleanly within `config/settings.py`.
   ```env
   # Storage mappings
   MONGO_URI="mongodb://localhost:27017" # or Atlas
   
   # Distribution mappings
   EMAIL_SENDER="your.automated.bot@gmail.com"
   EMAIL_PASSWORD="app_password_mapping_securely"
   ```

## Running Tests (TDD)

Per the project constitution, mock your external asynchronous `await` frameworks cleanly. Tests natively validate logic asserting that dictionaries physically unroll representing valid HTML boundaries avoiding standard live database injections dropping test constraints. 

- To execute standard mocked `async` TDD frameworks:
  ```bash
  pytest tests/unit/test_output_storage.py
  ```

## Local Prototyping

Ensure you natively define the `asyncio.run` boundaries initializing the logic correctly checking data models flawlessly:

```python
# test_live_storage.py (Do not commit)
from modules.output_storage import OutputStorage
import asyncio
from unittest.mock import MagicMock

async def test_email():
    try:
        # Defaults logically pointing down mapping internally inside
        storage = OutputStorage() 
        
        # Mocking explicit payloads mapped organically matching output
        mock_report = {
           "summary": "Standard test summary",
           "platform": "Zoom",
           "date": "2026-03-15",
           "action_items": [],
           "decisions": []
        }
        
        # Will dynamically test outbound mapping logic gracefully securely
        res = await storage.send_email(["test@example.com"], mock_report)
        print(f"Delivered: {res['sent']}")

    except Exception as e:
        print(f"Engine Failed: {str(e)}")

asyncio.run(test_email())
```
