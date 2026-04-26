# Data Model: Configuration & Environment Management

## Entities

### `Config` (Pydantic BaseSettings)

The primary configuration object managing typed environment variables.

**Fields**:
- `APP_TITLE` (str): FastAPI app title. Default: "AI Meeting Assistant API"
- `APP_HOST` (str): Server bind host. Default: "0.0.0.0"
- `APP_PORT` (int): Server bind port. Default: 8000
- `DEBUG` (bool): Enable debug mode. Default: False
- `MONGODB_URI` (str): MongoDB connection string. Default: "mongodb://localhost:27017"
- `MONGODB_DATABASE` (str): MongoDB database name. Default: "meeting_assistant"
- `STORAGE_BACKEND` (str): Default storage. Default: "database"
- `STT_PROVIDER` (str): Default STT provider. Default: "whisper"
- `WHISPER_API_KEY` (Optional[str]): OpenAI Whisper API key.
- `DEEPGRAM_API_KEY` (Optional[str]): Deepgram API key.
- `ASSEMBLYAI_API_KEY` (Optional[str]): AssemblyAI API key.
- `OPENAI_API_KEY` (Optional[str]): OpenAI LLM API key.
- `LLM_MODEL` (str): LLM model name. Default: "gpt-4o"
- `OBS_WEBSOCKET_HOST` (str): OBS WebSocket host. Default: "localhost"
- `OBS_WEBSOCKET_PORT` (int): OBS WebSocket port. Default: 4455
- `OBS_WEBSOCKET_PASSWORD` (str): OBS WebSocket password. Default: ""
- `EMAIL_SENDER` (Optional[str]): Sender email address.
- `EMAIL_PASSWORD` (Optional[str]): Sender app password.
- `GOOGLE_SHEETS_CRED_FILE` (str): Sheets service account key file. Default: "credentials.json"
- `GOOGLE_SHEETS_SPREADSHEET_ID` (Optional[str]): Target spreadsheet ID.
- `RECORDINGS_DIR` (str): Audio output directory. Default: "./recordings"
- `TRANSCRIPTS_DIR` (str): Transcript output directory. Default: "./transcripts"
- `SUMMARIES_DIR` (str): Summary output directory. Default: "./summaries"
- `LOGS_DIR` (str): Log file directory. Default: "./logs"
- `CORS_ORIGINS` (list[str]): Allowed CORS origins. Default: ["http://localhost:3000"]

**Validation Rules**:
- Type coercion is handled by Pydantic.
- Missing optional values evaluate to `None`.
- At startup, the API key corresponding to the selected `STT_PROVIDER` is validated. If missing, the app enters degraded mode.

### `SettingsOverride` (MongoDB Document)

User-configured settings persisted via the dashboard that override the Pydantic `Config`.

**Fields**:
- `user_id` (str, optional): For multi-tenant extensions (currently single-tenant).
- `stt_provider` (Optional[str]): Overrides `STT_PROVIDER`.
- `storage_backend` (Optional[str]): Overrides `STORAGE_BACKEND`.
- `email_sender` (Optional[str]): Overrides `EMAIL_SENDER`.
- `email_password` (Optional[str]): Overrides `EMAIL_PASSWORD`.

**Relationships**:
- Overrides properties of the base `Config` when `get_settings()` is called.
