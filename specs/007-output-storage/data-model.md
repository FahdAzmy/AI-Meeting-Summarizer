# Data Model: Output & Storage Module

This file defines the primary objects, attributes, and custom error enums utilized within the `output_storage.py` module context.

## 1. OutputStorage (Class Router)

The I/O controller orchestrating final persistence states.

- **backend** (`str`) - State mapping conditional routing (`"database"`, `"google_sheets"`).
- **email_sender** (`str`) - Active SMTP origin account mapped from settings.
- **email_password** (`str`) - Secure authorized credential.

## 2. Target Database Model mapping (`Meeting`)

While `Beanie` models are strictly defined within the broader models directory, the Storage module interacts intimately aligning attributes mapping natively down from the `MeetingReport`.

```python
# Values mapped into the internal system:
meeting.summary = report["summary"]
meeting.action_items = [ActionItem(**item) for item in report["action_items"]]
meeting.decisions = report["decisions"]
meeting.transcript = transcript["full_text"]
meeting.speaker_stats = SpeakerStats(**report["speaker_stats"]) # Casts only if it physically populated
meeting.duration_minutes = int(transcript["duration_seconds"] // 60)
meeting.status = MeetingStatus.COMPLETED # Shifts database flag from PROCESSING
```

## 3. Exceptions (Custom Error Structs)

To standardize pipeline abortion and the resulting error-payload outputs. Inherits from Pythons base `Exception`.

- `EmailDeliveryError` (`OS-001`): Tripped mapping global SMTP failures or authentication blockades natively avoiding silent failures dynamically.
- `SheetsWriteError` (`OS-002`): Fired actively triggering the failover routines dropping outputs directly down into standard CSVs gracefully mapping data securely.
- `DatabaseWriteError` (`OS-003`): Fired actively natively representing complete DB engine dropping during `await meeting.save()` limits natively returning `HTTP 500`.
- `InvalidBackendError` (`OS-004`): Fired validating string assignments rejecting unconfigured parameters strictly mapped within the ecosystem properly.
