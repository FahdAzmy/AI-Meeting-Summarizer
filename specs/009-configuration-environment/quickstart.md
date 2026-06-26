# Quickstart: Configuration & Environment Management

## Overview
This feature implements centralized configuration using Pydantic `BaseSettings` with a layered override hierarchy: Defaults -> `.env` -> Environment Variables -> Dashboard Overrides.

## 1. Setup Environment
1. Copy the sample environment file to create your local configuration:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in any required API keys (e.g., `WHISPER_API_KEY` if using Whisper).
   - *Note: Only the API key for your active STT/LLM provider is required. Others can be left blank.*

## 2. Using Configuration in Code
Import the `get_settings()` dependency (which handles the override hierarchy) instead of importing `config` directly in your endpoints or services:

```python
from config.settings import get_settings

async def my_service():
    settings = await get_settings()
    print(f"Using STT Provider: {settings.STT_PROVIDER}")
```

## 3. Degraded Mode
If you start the backend without a required API key, the dashboard will still load. The pipeline will be blocked and will report an error until you provide the missing key either in the `.env` file or via the Dashboard Settings page.
