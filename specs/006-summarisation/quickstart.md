# Quickstart: Summarisation Module

This guide provides developer instructions to run local implementations and test environments for the `summarisation.py` API module.

## Prerequisites

- Python `3.10+`
- Subscribed or Free-Tier developer accounts configured for requested LLM providers:
  - OpenAI GPT Key

## Setup Python

1. **Navigate to the core project directory**
   ```bash
   cd project
   ```

2. **Install Python dependencies**
   Ensure SDKs target standard installation maps.
   ```bash
   pip install openai pydantic
   ```

3. **Configure the Environment Maps**
   Load the LLM execution values natively into local `.env` keys targeting `config/settings.py`.
   ```env
   OPENAI_API_KEY="sk-..."
   LLM_MODEL="gpt-4o"
   ```

## Running Tests (TDD)

Per the project constitution, mock your external LLM calls! We do NOT trigger live ChatGPT completions inside CI because they are inherently non-deterministic and very expensive.

- To execute mocked TDD tests (which utilize the `responses` or `mock` libraries checking your analytical math algorithms):
  ```bash
  pytest tests/unit/test_summarisation.py
  ```

## Local Prototyping

Ensure you have a pre-generated mock transcript dictionary ready:

```python
# test_live_summary.py (Do not commit)
from modules.summarisation import Summarisation

try:
    bot = Summarisation() 
    
    mock_transcript = {
       "full_text": "Hey Alice, can you please have those TPS reports completed by Friday? Yes, absolutely Bob.",
       "segments": [],
       "diarisation_available": False,
       "duration_seconds": 15.0
    }
    
    payload = bot.generate_report(mock_transcript)
    
    print(payload["summary"])
    print(payload["action_items"])

except Exception as e:
    print(f"Engine Failed: {str(e)}")
```
