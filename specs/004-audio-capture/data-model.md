# Data Model: Audio Capture Module

This file defines the primary objects, attributes, and custom error enums utilized within the `audio_capture.py` module context.

## 1. AudioCapture (Class)

The client binding mapping the WebSocket connection to OBS.

- **client** (`obsws_python.ReqClient`) - The active socket configuration targeting OBS.
- **host** (`str`) - WebSocket IP (e.g. `localhost`).
- **port** (`int`) - WebSocket Port (e.g. `4455`).
- **password** (`str`) - WebSocket authorization password.

## 2. Exceptions (Custom Error Structs)

To standardize pipeline abortion and the resulting error-payload outputs. Inherits from Pythons base `Exception`.

- `OBSConnectionError` (`AC-001`): Socket timeout tracking bad credentials or bad port.
- `OBSNotRunning` (`AC-002`): Fired actively by the `healthcheck` function avoiding the main bot start.
- `RecordingStartError` (`AC-003`): OBS throws a failure message back via the socket upon `client.start_record()`.
- `RecordingStopError` (`AC-004`): OBS throws a failure message upon halting. 
- `EmptyRecordingError` (`AC-005`): File size checking post-execution yields `0` bytes (or path is unresolvable).
