# Data Model: Zoom Meeting SDK Integration

**Feature**: 011-zoom-meeting-sdk

## Config Settings (Environment)

The following new environment variables will be added to the backend `config/settings.py` (`Config` class):

| Field | Type | Description |
|-------|------|-------------|
| `ZOOM_SDK_CLIENT_ID` | String | Public identifier for the Zoom Meeting SDK App. |
| `ZOOM_SDK_CLIENT_SECRET` | String | Secret key used to sign JWT signatures. Never exposed to frontend. |

## Internal Entities

### `ZoomMeetingDetails`

Extracted from a parsed Zoom URL.

| Field | Type | Description |
|-------|------|-------------|
| `meeting_number` | String | The numeric identifier of the meeting. |
| `passcode` | String | The optional meeting password. |

### `ZoomSignatureRequest`

Payload sent to the backend to generate a signature.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `meeting_number` | String | The numeric meeting identifier. | Required |
| `role` | Integer | 0 for attendee, 1 for host. | Default: 0 |

### `ZoomSignatureResponse`

Payload returned by the backend containing the JWT signature.

| Field | Type | Description |
|-------|------|-------------|
| `signature` | String | The JWT token signed with `HS256`. |
| `sdk_key` | String | The `ZOOM_SDK_CLIENT_ID` to be used by the frontend SDK. |

## State Transitions

The orchestrator's meeting state remains mostly unchanged (`JOINING` -> `RECORDING` -> `TRANSCRIBING` -> `SUMMARISING` -> `COMPLETED`). 

The main difference is that in the `JOINING` state for Zoom URLs, instead of synchronously blocking on `MeetingAccess._join_zoom()`, the orchestrator will trigger the frontend page and wait for an async signal (either a database status update or a webhook callback) that the meeting has entered the `RECORDING` phase.
