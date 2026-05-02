# Research: Zoom Meeting SDK Integration

**Date**: 2026-05-02  
**Spec**: [spec.md](spec.md)

## 1. Zoom Meeting SDK vs Other Zoom Developer Products

| Product | Purpose | Supports Standard Zoom Meetings? | Raw Audio Access? |
|---------|---------|----------------------------------|-------------------|
| **Meeting SDK (Web)** | Embed Zoom meeting UI in a web page | ✅ Yes | ❌ No |
| **Meeting SDK (Windows/Linux)** | Native app with raw data APIs | ✅ Yes | ✅ Yes (PCM 16LE) |
| **Video SDK** | Custom video sessions (not Zoom meetings) | ❌ No | ✅ Yes |
| **RTMS (Real-Time Media Streams)** | WebSocket-based raw media from meetings | ✅ Yes | ✅ Yes |
| **Zoom REST API** | Meeting management (CRUD, recordings) | N/A (management) | Cloud recordings only |

### Why Meeting SDK (Web)?

- Our project is a **web-based** application (Next.js frontend + FastAPI backend).
- We need to join **standard Zoom meetings** (not custom sessions).
- We do NOT need raw audio from the SDK — we already have OBS-based recording.
- The Web SDK is the **lowest friction** path: npm package + JWT auth.
- No need for native C++ SDK compilation (Windows/Linux SDK), no WebSocket server setup (RTMS).

### Limitations Accepted

- **No headless mode**: The SDK requires a browser page with DOM. This is fine — our pipeline already opens a Chrome window for Selenium.
- **No raw audio**: OBS continues to handle recording. The SDK only handles **reliable meeting join** and **event-driven end detection**.
- **Terms of Use**: Zoom's ToS prohibit "AI bots" using the Meeting SDK. However, our use case (joining as an attendee to capture audio externally) operates in a gray area. The SDK is strictly used for join/leave — not for embedded recording or AI processing.

## 2. SDK Authentication Deep Dive

### App Registration Flow

```
Zoom Marketplace → Develop → Build App → General App → Create
                                           ↓
                                    Basic Information
                                    (App name, contact)
                                           ↓
                                    Features → Embed
                                    (Toggle "Meeting SDK" ON)
                                           ↓
                                    App Credentials
                                    (Client ID + Client Secret)
                                           ↓
                                    Development / Production
                                    (Separate credential pairs)
```

### JWT Payload Specification

| Field      | Type   | Description                                      |
|------------|--------|--------------------------------------------------|
| `appKey`   | string | SDK Client ID                                    |
| `mn`       | string | Meeting number (numeric)                         |
| `role`     | int    | 0 = attendee, 1 = host                          |
| `iat`      | int    | Issued-at timestamp (epoch seconds)              |
| `exp`      | int    | Expiration (min 30 min after iat, max 48 hours)  |
| `tokenExp` | int    | Same as `exp`                                    |

**Algorithm**: HS256  
**Signing key**: SDK Client Secret  

### ZAK Token (Not Needed for Our Case)

The ZAK (Zoom Access Key) token is only required when:
- **Starting** a meeting as host (role=1)
- Joining a meeting that requires **authenticated users only**

For our use case (joining as an attendee with role=0), the JWT signature alone is sufficient.

## 3. Frontend SDK Integration Details

### Package: `@zoom/meetingsdk`

```bash
npm install @zoom/meetingsdk --save
```

### Client View (Recommended for Our Use Case)

Client View renders the **full Zoom meeting experience** — identical to zoom.us web client. This is simpler to implement and provides the complete meeting UI without custom layout work.

```javascript
import { ZoomMtg } from '@zoom/meetingsdk';

// 1. Set the library path for WASM assets
ZoomMtg.setZoomJSLib('https://source.zoom.us/5.18.0/lib', '/av');

// 2. Preload WebAssembly
ZoomMtg.preLoadWasm();
ZoomMtg.prepareWebSDK();

// 3. Initialize + Join
ZoomMtg.init({
  leaveUrl: '/meeting-ended',
  success: () => {
    ZoomMtg.join({
      signature: jwtFromBackend,
      meetingNumber: '1234567890',
      userName: 'AI Summarizer',
      passWord: 'meetingPasscode',
      sdkKey: 'YOUR_SDK_CLIENT_ID',
      success: (res) => console.log('Joined!', res),
      error: (err) => console.error('Join failed', err),
    });
  },
  error: (err) => console.error('Init failed', err),
});
```

### Component View (Alternative)

Component View provides modular UI components that can be embedded in custom layouts. However, it:
- Is **desktop-only** (no mobile support)
- Requires more design/layout work
- May lack some features available in Client View

**Decision: Use Client View** for simplicity and feature completeness.

### Key SDK Events

| Event | When Fired | Our Action |
|-------|------------|------------|
| `meeting-join` | Bot successfully joins | Update status to `RECORDING` |
| `meeting-end` / `meeting-leave` | Meeting ends or bot leaves | Trigger post-processing pipeline |
| `participant-join` | A participant joins | Log (for participant tracking) |
| `participant-leave` | A participant leaves | Check if alone → trigger grace period |

## 4. URL Parsing Patterns

### Standard Zoom URLs

| Format | Example | Meeting Number | Passcode |
|--------|---------|---------------|----------|
| Standard | `https://zoom.us/j/1234567890` | `1234567890` | (none) |
| With password | `https://zoom.us/j/1234567890?pwd=abc123` | `1234567890` | `abc123` |
| Subdomain | `https://company.zoom.us/j/9876543210` | `9876543210` | (none) |
| With subdomain + pwd | `https://myorg.zoom.us/j/5555555555?pwd=xyz789` | `5555555555` | `xyz789` |

### Unsupported Zoom URL Formats

| Format | Example | Why Unsupported |
|--------|---------|-----------------|
| Vanity URL | `https://zoom.us/my/username` | No numeric meeting ID; requires API lookup |
| Personal link | `https://zoom.us/s/1234567890` | Webinar format, different join flow |

### Regex Pattern

```
https?://(?:[a-z0-9-]+\.)?zoom\.us/j/(\d+)(?:\?pwd=([a-zA-Z0-9]+))?
```

## 5. Dependencies Impact

### Backend (Python)

| Package | Version | Purpose | Size Impact |
|---------|---------|---------|-------------|
| `PyJWT` | >=2.8.0 | JWT signature generation | ~50KB (minimal) |

Note: `python-jose[cryptography]` is already in `requirements.txt` and could potentially be used instead of `PyJWT`. However, `PyJWT` is the library specifically referenced in Zoom's official documentation. Either library works for HS256 signing.

### Frontend (Node.js)

| Package | Version | Purpose | Size Impact |
|---------|---------|---------|-------------|
| `@zoom/meetingsdk` | latest | Zoom Web SDK | ~15-20MB (includes WASM) |

The `@zoom/meetingsdk` package is large due to the embedded WebAssembly module. This is loaded on-demand only on the Zoom meeting page, not on every page load.

## 6. Security Considerations

| Risk | Mitigation |
|------|------------|
| Client Secret exposure in frontend | Generate JWT exclusively on backend; never send secret to frontend |
| JWT token theft | Short expiry (2h); tokens are meeting-specific (cannot join other meetings) |
| Unauthorized signature requests | Protect `/api/zoom/signature` with authentication middleware |
| SDK version vulnerabilities | Monitor Zoom SDK release notes; pin to known-good versions |

## 7. Alternative Approaches Considered

### Option A: Zoom RTMS (Real-Time Media Streams)
- **Pro**: Direct raw audio access via WebSocket → could replace OBS entirely.
- **Con**: Requires server-side WebSocket infrastructure, significantly more complex.
- **Con**: Only available for Zoom Video SDK, not Meeting SDK.
- **Decision**: Rejected for MVP. Could be explored in a future phase.

### Option B: Zoom Meeting SDK for Windows (Native)
- **Pro**: Full raw audio/video access (PCM, I420).
- **Con**: Requires C++ compilation, Windows-only server, drastically different architecture.
- **Decision**: Rejected. Our stack is Python + Node.js, not C++.

### Option C: Keep Selenium (Status Quo)
- **Pro**: No new dependencies, no Zoom Marketplace registration.
- **Con**: ~60-70% reliability, frequent maintenance, bot detection risks.
- **Decision**: Not viable for production. Selenium remains as fallback only.
