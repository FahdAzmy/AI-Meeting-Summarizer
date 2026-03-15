# Phase 0: Outline & Technical Research

## Recording Infrastructure (OBS vs Native PyAudio)

**Decision**: Integrate with **OBS Studio** via `obsws_python`.
**Rationale**: Native Python libraries capturing system-level "desktop audio" cross-platform (Windows, MacOS, Linux) are notoriously fragile and require significant custom driver handling (e.g., virtual audio cables or Loopback API manipulation). By delegating this to OBS Studio—a battle-tested open-source broadcasting software—the Python module only needs to pass "record" and "stop" commands via local WebSockets, dramatically simplifying the repository. 
**Alternatives considered**: Using `PyAudio` with Virtual Cables. Rejected because routing the specific browser output to PyAudio frequently detaches or fails natively without heavy OS-level configuration out-of-scope for the pipeline execution.

## File Format Guarantee

**Decision**: Enforce `.wav` format configuration inside OBS (44100 Hz, Stereo).
**Rationale**: Downstream Speech-to-Text services (like Whisper) perform significantly better on uncompressed raw waveforms. MP3 encoding artifacts degrade diarization and translation quality. Storage considerations (size) are negligible locally since the file is usually transcribed immediately and can be compressed post-pipeline.

## Healthcheck Execution Path

**Decision**: Enforce a strict `healthcheck()` boolean block prior to invoking `start()`.
**Rationale**: The most common point of failure for this specific pipeline module isn't bad inputs—it's that OBS isn't currently running, or the WebSocket server hasn't booted. By forcing the module to poll a `client.get_version()` command during instantiation or right before execution, we catch 99% of fatal pipeline collapses before the Selenium browser even clicks "Join" on the meeting, avoiding silent failure outcomes.
