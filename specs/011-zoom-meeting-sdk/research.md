# Research: Zoom Meeting SDK Integration

**Date**: 2026-05-03
**Spec**: [spec.md](spec.md)

## 1. Zoom Meeting SDK vs Other Approaches

### Why Meeting SDK (Web)?
- **Decision**: Use the Zoom Meeting SDK for Web (`@zoom/meetingsdk`).
- **Rationale**: We need to join standard Zoom meetings programmatically. The Web SDK allows us to embed a Zoom meeting client into a web page and authenticate via a server-generated JWT. This eliminates brittle UI scraping and avoids automated browser detection.
- **Alternatives considered**:
  - *Zoom RTMS (Real-Time Media Streams)*: Provides raw WebSocket audio access, but requires setting up a complex WebSocket server and only works for custom Video SDK sessions, not standard Zoom meetings.
  - *Native Windows SDK*: Provides raw PCM audio, but requires C++ compilation and deviates too much from the current web-centric architecture.
  - *Status Quo (Selenium)*: Too fragile, frequently blocked by Zoom, and slow end-of-meeting detection.

### Constraint: Audio Capture
- **Decision**: Continue using OBS for audio capture.
- **Rationale**: The Zoom Web SDK *does not* provide access to the raw audio stream. We will use the SDK purely to get a reliable, programmatic presence in the meeting and receive instant native events (like meeting end), while the existing OBS component records the system audio.

## 2. Authentication Flow

- **Decision**: Use a backend-generated JWT token to authenticate the SDK.
- **Rationale**: The Zoom App Marketplace provides a Client ID and Client Secret for "General Apps" with the "Meeting SDK" feature enabled. The Client Secret must remain on the backend. The frontend will hit a new public endpoint (`/api/zoom/signature`) to get a short-lived token (expiring in 2 hours) signed with `HS256`.

## 3. URL Parsing

- **Decision**: Use regular expressions to extract the meeting ID and passcode.
- **Rationale**: Zoom URLs follow standard patterns (`https://zoom.us/j/1234567890?pwd=abc123` or `https://company.zoom.us/j/1234567890`). A regex `r"https?://(?:[a-z0-9-]+\.)?zoom\.us/j/(\d+)(?:\?pwd=([a-zA-Z0-9]+))?"` will reliably extract the numeric meeting identifier and passcode.

## 4. Frontend Integration

- **Decision**: Create a dedicated Next.js background page (`/zoom-meeting`).
- **Rationale**: The SDK requires a DOM to render. Since the orchestrator will open this page, we can run it in a background tab that the user doesn't see, maintaining a clean dashboard UX while keeping the SDK active.

## 5. Fallback Mechanism

- **Decision**: Graceful fallback to Selenium.
- **Rationale**: If the `ZOOM_SDK_CLIENT_ID` or `ZOOM_SDK_CLIENT_SECRET` are not configured in `.env`, the system should log a warning and fall back to the existing Selenium browser-automation path to ensure the system still functions out of the box without requiring Zoom Marketplace setup.
