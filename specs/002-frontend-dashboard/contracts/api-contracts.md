# API Contracts (Frontend Dashboard)

This contract defines the expected endpoints the frontend service calls on the distinct Python FastAPI backend. The frontend relies on these static HTTP/JSON boundaries to fetch and submit state data.

**Base URL**: `http://localhost:8000/api`

## POST `/join`

Initiates the backend processing for a submitted meeting link.
**Payload:**
```json
{
  "meeting_link": "https://meet.google.com/abc-defg-hij",
  "emails": ["user1@example.com", "user2@example.com"]
}
```
**Response:** `200 OK`
```json
{
  "session_id": "20260315_120304"
}
```

---

## GET `/status/:session_id`

Provides real-time polling updates for an active pipeline run.
**Response:** `200 OK`
```json
{
  "session_id": "20260315_120304",
  "status": "summarising",
  "step": 4,
  "total_steps": 6,
  "message": "Generating the LLM analytical summary..."
}
```

---

## GET `/meetings`

Returns an array of truncated meeting objects for the history view component.
**Response:** `200 OK`
```json
[
  {
    "id": "abc-1234",
    "meeting_link": "https://zoom.us/j/12345678",
    "platform": "zoom",
    "date": "2026-03-14T15:00:00Z",
    "duration_minutes": 45,
    "summary": "Discussed Q2 planning...",
    "status": "completed"
  }
]
```

---

## GET `/meetings/:id`

Retrieves the deeply embedded detailed payload containing the full transcript, specific sub-metrics, and decisions.
**Response:** `200 OK`
```json
{
  "id": "abc-1234",
  "meeting_link": "https://zoom.us/j/12345678",
  "platform": "zoom",
  "date": "2026-03-14T15:00:00Z",
  "duration_minutes": 45,
  "participants": ["dev@example.com"],
  "transcript": "Full literal text block here...",
  "summary": "Full formatted markdown summary here...",
  "status": "completed",
  "action_items": [
    {
      "assignee": "Alice",
      "task": "Update backend docs",
      "deadline": null
    }
  ],
  "decisions": ["Adopt Next.js App Router"],
  "speaker_stats": null
}
```
*Note: Returns 404 if ID doesn't exist.*

---

## GET `/settings`

Gets the global preferences.
**Response:** `200 OK`
```json
{
  "storage_backend": "database",
  "stt_provider": "whisper",
  "email_sender": "ai-assistant@company.com",
  "email_password": "***"
}
```

---

## POST `/settings`

Updates the global preferences.
**Payload:**
```json
{
  "storage_backend": "google_sheets",
  "stt_provider": "deepgram"
}
```
**Response:** `200 OK` *(Returns full updated settings mapping GET payload)*
