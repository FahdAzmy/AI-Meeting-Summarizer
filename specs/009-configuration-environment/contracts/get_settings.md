# Interface Contract: Configuration

## `get_settings()` Internal Interface

This function serves as the central point for resolving configuration overrides across the backend application.

**Purpose**: Resolves the layered configuration hierarchy by merging Pydantic `BaseSettings` (loaded from `.env` and environment variables) with any user overrides persisted in MongoDB.

**Signature**:
```python
async def get_settings() -> Config:
    ...
```

**Returns**:
- An instance of the `Config` class containing the finalized, type-checked configuration values.

**Usage Requirements**:
- Must be called asynchronously.
- Caches the base Pydantic configuration but fetches database overrides dynamically to ensure runtime updates take effect immediately.

**Failure Modes**:
- If the database is unreachable, it logs a warning and returns the base `Config` (falling back to `.env`/env vars).
- Validates the resolved settings. If a required value (e.g., the active STT provider's API key) is missing, it raises a custom `ConfigurationError` that the FastAPI exception handler translates into a degraded-mode HTTP response indicating the missing configuration.
