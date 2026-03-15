# Data Model: Pipeline Orchestrator

This file defines the primary objects, attributes, and explicit status states mapped during the `orchestrator.py` module execution context.

## 1. Orchestrated Sequence (Pipeline)

The sequence controls exact Python instantiations dynamically managing object relationships explicitly avoiding global scopes natively.

```python
# Pseudo-Sequence
meeting = Meeting(session=...)
await meeting.insert()

try:
    access = MeetingAccess()
    capture = AudioCapture()
    
    # Bounded Thread Blocks
    await asyncio.to_thread(access.join)
    await asyncio.to_thread(capture.start) 
    
    # Native Async Blocks
    transcriber = Transcription()
    transcript = transcriber.transcribe() # Wait block
    
    # Continual Status Mutation
    meeting.status = MeetingStatus.TRANSCRIBING
    await meeting.save()
```

## 2. Tracking State (`MeetingStatus` Enum)

The internal system boundary markers. The frontend directly reflects these metrics graphically.

- `JOINING`: The robot is actively booting Selenium and rendering the browser organically.
- `RECORDING`: Selenium is successfully connected mapping perfectly inside the meeting room passively monitoring.
- `TRANSCRIBING`: The meeting ended natively, and the system is transferring `.wav` files mapping text dynamically.
- `SUMMARISING`: Native text structurally processed through the LLM architectures perfectly formatting Markdown.
- `DELIVERING`: LLM text mathematically converting formatting securely deploying down outward SMTP bounds naturally.
- `COMPLETED`: Pipeline structurally concludes and halts correctly.
- `FAILED`: Used identically identifying structural drops avoiding infinite loops structurally inside.
