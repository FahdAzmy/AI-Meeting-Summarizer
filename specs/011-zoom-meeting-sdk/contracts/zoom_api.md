# Zoom API Contracts

## `POST /api/zoom/signature`

Generates a Zoom Meeting SDK authorisation token using the backend Client Secret.
This endpoint is public (no authentication required).

### Request Body (`ZoomSignatureRequest`)

```json
{
  "meeting_number": "1234567890",
  "role": 0
}
```

- `meeting_number`: String (Required). The numeric ID of the Zoom meeting.
- `role`: Integer (Optional). 0 for attendee, 1 for host. Default is 0.

### Response

#### 200 OK

```json
{
  "signature": "eyJhbGciOiJIUzI1NiJ9.eyJhcHBLZXkiOiJteV9hcHBfa2V5Iiwic2RrS2V5IjoibXlfYXBwX2tleSIsIm1uIjoiMTIzNDU2Nzg5MCIsInJvbGUiOjAsImlhdCI6MTcxNDc0MjgwMCwiZXhwIjoxNzE0NzUwMDAwLCJ0b2tlbkV4cCI6MTcxNDc1MDAwMH0.1234567890abcdef",
  "sdk_key": "YOUR_CLIENT_ID"
}
```

- `signature`: The JWT token string to pass to `ZoomMtg.join()`.
- `sdk_key`: The Client ID to pass to `ZoomMtg.init()` and `ZoomMtg.join()`.

#### 500 Internal Server Error

```json
{
  "detail": "Zoom SDK credentials not configured on the server."
}
```
