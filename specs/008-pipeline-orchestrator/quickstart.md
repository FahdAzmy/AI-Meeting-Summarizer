# Quickstart: Pipeline Orchestrator

This guide provides developer instructions to run local implementations testing the high-level orchestration boundaries naturally without actually deploying individual STT services mapping logic organically.

## Prerequisites

- Python `3.10+`
- All subordinate module mappings functional (`requests`, `beanie`, `selenium`, `aiosmtplib`, `openai`)

## Setup Python

1. **Navigate to the core project directory**
   ```bash
   cd project
   ```

2. **Validate FastApi Dependencies**
   ```bash
   pip install fastapi uvicorn beanie
   ```

## Running Tests (TDD)

Per the project constitution, mock your module loops accurately. You are testing the **Orchestrator** (the `run_pipeline` task itself), not Selenium, OpenAI, or the DB. Native tests should verify the function organically steps through `meeting.status` dynamically mapping exceptions accurately!

- To execute mocked asynchronous orchestration tests evaluating internal state switches flawlessly:
  ```bash
  pytest tests/unit/test_orchestrator.py
  ```

## Local Prototyping

Ensure you validate the FastAPI background-task boundaries organically launching the web server natively:

```python
# test_live_fastapi.py (Do not commit)
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from orchestrator import run_pipeline

app = FastAPI()

@app.post("/trigger")
async def trigger_endpoint(link: str, background_tasks: BackgroundTasks):
    
    # Safely deploys the 60+ minute loop completely detached structurally natively
    background_tasks.add_task(run_pipeline, meeting_link=link, storage="database")
    
    # Instantly returns standard web codes natively preventing locking
    return {"message": "Meeting successfully scheduled. The bot is joining now."}

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
```
