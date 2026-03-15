# Quickstart: Audio Capture Module

This guide provides developer instructions to run local implementations and test environments for the OBS WebSocket based `audio_capture` module.

## Prerequisites

- Python `3.10+`
- **OBS Studio v30+** installed on the local machine.
- OBS WebSocket Server enabled.

## Setup Python

1. **Navigate to the core project directory**
   ```bash
   cd project
   ```

2. **Install Python dependencies**
   Ensure `obsws-python` is present in your ecosystem.
   ```bash
   pip install obsws-python
   ```

## Setup OBS Studio

1. Open OBS Studio.
2. Navigate to **Tools -> WebSocket Server Settings**.
3. Check the box **Enable WebSocket server**.
4. Set Server Port: `4455` (default).
5. Check **Enable Authentication** and set a dummy password (e.g., `test1234`).
6. Update your local Python environment (`Config`) with these credentials.

## Running Tests (TDD)

Per the project constitution, mock your external calls! Do not spin up an actual OBS Studio connection during unit tests to ensure fast CI runs. 

- To execute mocked TDD tests (which will assert socket calling counts and exceptions):
  ```bash
  pytest tests/unit/test_audio_capture.py
  ```

## Local Prototyping

Ensure OBS Studio is open, then run:

```python
# test_live_audio.py (Do not commit)
from modules.audio_capture import AudioCapture
import time

bot = AudioCapture()

if bot.healthcheck():
    print("OBS Responding. Starting mock recording for 5 seconds...")
    bot.start()
    time.sleep(5)
    file_path = bot.stop()
    print(f"Captured: {file_path}")
else:
    print("OBS disconnected or failing healthcheck.")
```
