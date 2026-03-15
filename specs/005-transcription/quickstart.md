# Quickstart: Transcription Module

This guide provides developer instructions to run local implementations and test environments for the `transcription.py` API module.

## Prerequisites

- Python `3.10+`
- Subscribed or Free-Tier developer accounts configured for requested STT providers:
  - OpenAI (Whisper) Key
  - Deepgram Key
  - AssemblyAI Key (Optional)

## Setup Python

1. **Navigate to the core project directory**
   ```bash
   cd project
   ```

2. **Install Python dependencies**
   Ensure SDKs target standard installation maps.
   ```bash
   pip install requests openai deepgram-sdk assemblyai
   ```

3. **Configure the Environment Maps**
   The application requires the active keys natively loaded to perform calls.
   Ensure these map directly into your local `.env` file targeting `config/settings.py`.
   ```env
   WHISPER_API_KEY="sk-..."
   DEEPGRAM_API_KEY="..."
   ASSEMBLYAI_API_KEY="..."
   ```

## Running Tests (TDD)

Per the project constitution, mock your external calls! Do not spam live third-party APIs aggressively inside CI. Test coverage asserts the exception handling loops execute appropriately inside simulated outages.

- To execute mocked TDD tests (which utilize the `responses` or `mock` libraries):
  ```bash
  pytest tests/unit/test_transcription.py
  ```

## Local Prototyping

When you have a valid `.wav` file ready to evaluate your keys natively:

```python
# test_live_transcription.py (Do not commit)
from modules.transcription import Transcription

try:
    bot = Transcription(provider="deepgram") # Defaults to whisper if None
    payload = bot.transcribe("./mock_audio.wav")
    
    # Payload now safely maps to the TranscriptResult spec schema natively
    print(payload["full_text"])
    print(f"Total Segments Detected: {len(payload['segments'])}")

except Exception as e:
    print(f"Engine Failed: {str(e)}")
```
