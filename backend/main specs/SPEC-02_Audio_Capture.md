# SPEC-02: Audio Capture Module

| Field            | Details                                  |
|------------------|------------------------------------------|
| **File**         | `modules/audio_capture.py`               |
| **Class**        | `AudioCapture`                           |
| **Traceability** | FR3, FR4, NFR6                           |
| **Version**      | 1.0                                      |
| **Date**         | March 12, 2026                           |

---

## 02.1 Class Interface

```python
class AudioCapture:
    def __init__(self) -> None
    def start(self) -> None
    def stop(self) -> str          # → returns audio file path
    def healthcheck(self) -> bool
```

---

## 02.2 Method Specifications

### `__init__()` **[M]**
- Connects to OBS via `obsws_python.ReqClient(host, port, password)` using values from `Config`.
- Raises `OBSConnectionError` if connection fails.

### `start()` **[M]**
1. Call `healthcheck()` — abort if OBS is not ready.
2. Ensure output directory (`Config.RECORDINGS_DIR`) exists.
3. Execute `client.start_record()`.
4. Poll `client.get_record_status()` to confirm recording is active.
5. Log start timestamp.

### `stop() → str` **[M]**
1. Execute `client.stop_record()`.
2. Retrieve output file path from OBS response.
3. Verify file exists and size > 0 bytes.
4. Return absolute file path as string.

### `healthcheck() → bool` **[M]**
1. Attempt `client.get_version()` — verify OBS is responsive.
2. Check that a valid audio source is configured.
3. Return `True` if all checks pass, `False` otherwise.

---

## 02.3 Pre-flight Checks

| Check                          | Method                                  | Failure Action          |
|--------------------------------|-----------------------------------------|-------------------------|
| OBS process is running         | OBS WebSocket `get_version()`           | Raise `OBSNotRunning`   |
| WebSocket is reachable         | TCP connection to `host:port`           | Raise `OBSConnectionError` |
| Audio source is mapped         | `get_input_list()` contains audio source| Log warning             |
| Output directory is writable   | `os.access(dir, os.W_OK)`              | Create dir or raise     |

---

## 02.4 Output Format

| Property         | Value                                              |
|------------------|----------------------------------------------------|
| Default format   | `.wav` (lossless, best for STT accuracy)           |
| Alternative      | `.mp3` (smaller size, configurable via OBS)        |
| Sample rate      | 44100 Hz (OBS default)                             |
| Channels         | Stereo (system audio capture)                      |
| File naming      | `{session_id}.wav` (e.g., `20260312_143015.wav`)   |
| Storage path     | `./recordings/{filename}`                          |

---

## 02.5 Error Codes

| Code    | Name                   | Trigger                                         |
|---------|------------------------|-------------------------------------------------|
| AC-001  | `OBSConnectionError`   | Cannot connect to OBS WebSocket.                |
| AC-002  | `OBSNotRunning`        | OBS Studio is not running.                      |
| AC-003  | `RecordingStartError`  | OBS failed to start recording.                  |
| AC-004  | `RecordingStopError`   | OBS failed to stop recording.                   |
| AC-005  | `EmptyRecordingError`  | Output file is 0 bytes (no audio captured).     |

---

## 02.6 Acceptance Criteria

| #  | Criteria                                                     | Verified |
|----|--------------------------------------------------------------|----------|
| 1  | OBS starts recording when pipeline begins.                   | ☐        |
| 2  | OBS stops recording and outputs a valid audio file.          | ☐        |
| 3  | Healthcheck detects OBS not running.                         | ☐        |
