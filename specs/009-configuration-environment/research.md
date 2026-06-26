# Research: Configuration & Environment Management

## Overview

This document resolves technical details for the Configuration & Environment Management feature, as guided by `SPEC-07` and the `009-configuration-environment` spec.

## Technical Decisions

### Configuration Library

**Decision**: Use `pydantic-settings` (`BaseSettings`).
**Rationale**: Pydantic's `BaseSettings` provides robust type validation, automatic type coercion, and built-in support for reading from environment variables and `.env` files. It natively integrates with FastAPI, the framework used for the backend, making dependency injection and validation seamless.
**Alternatives considered**: 
- `python-decouple`: Lacks the deep typing integration provided by Pydantic.
- `Dynaconf`: Powerful but introduces unnecessary complexity and a heavier footprint for the specific requirements of this project.

### Settings Override Hierarchy

**Decision**: Implement a custom getter `get_settings()` that first queries the MongoDB database for dashboard-persisted overrides, and falls back to the Pydantic `Config` instance.
**Rationale**: Pydantic handles defaults -> `.env` -> environment variables out of the box. To add the "dashboard-persisted settings" layer at the top of the hierarchy, reading from the database dynamically at runtime ensures that changes made via the UI take immediate effect without an application restart.
**Alternatives considered**: 
- Modifying the `.env` file programmatically from the dashboard: Rejected because it requires write access to the filesystem and requires restarting the server to reload `BaseSettings`.

### Secrets Masking in Logs

**Decision**: Implement a custom Pydantic model dump or custom formatter for the configuration object that replaces sensitive field values (fields containing "KEY" or "PASSWORD") with `***` before logging.
**Rationale**: Ensures that accidental logging of the configuration object does not leak credentials.

### Degraded Startup Mode

**Decision**: If a required API key (for the currently selected provider) is missing, the backend will catch the validation error during pipeline initialization, rather than at application startup. The FastAPI app starts successfully, serving the dashboard, but endpoints triggering the pipeline will return a specific error indicating the missing configuration, allowing the UI to prompt the user.
**Rationale**: Fulfills the requirement that the dashboard remains accessible so the user can enter the missing key.
