"""
config/settings.py
------------------
Centralised environment-variable configuration for the AI Meeting Summarizer
pipeline.

Sections
--------
  - OBS / Audio Capture  : AC-specific WebSocket credentials & output path
  - STT                  : Speech-to-text API keys (Whisper, Deepgram, AssemblyAI)
  - LLM                  : Provider-agnostic LLM settings (any OpenAI-compatible API)
  - Storage & Distribution: MongoDB URI, SMTP sender credentials (Output Storage Module)

Provider Examples (set in .env)
--------------------------------
  OpenAI      : LLM_BASE_URL=https://api.openai.com/v1
  OpenRouter  : LLM_BASE_URL=https://openrouter.ai/api/v1
  Groq        : LLM_BASE_URL=https://api.groq.com/openai/v1
  Mistral     : LLM_BASE_URL=https://api.mistral.ai/v1
  Ollama      : LLM_BASE_URL=http://localhost:11434/v1

Usage
-----
    from config.settings import Config

    cfg = Config()  # reads from environment / .env file automatically
"""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application-wide settings resolved from environment variables or .env."""

    # ------------------------------------------------------------------
    # OBS WebSocket – Audio Capture Module
    # ------------------------------------------------------------------
    OBS_HOST: str = Field(
        default="localhost", description="OBS WebSocket server hostname."
    )
    OBS_PORT: int = Field(default=4455, description="OBS WebSocket server port.")
    OBS_PASSWORD: str = Field(
        default="", description="OBS WebSocket authentication password."
    )

    # Directory where OBS will save the raw recordings.
    # Defaults to <project_root>/recordings/
    RECORDINGS_DIR: str = Field(
        default=str(Path(__file__).resolve().parent.parent / "recordings"),
        description="Absolute path to the directory that stores audio recordings.",
    )

    # ------------------------------------------------------------------
    # STT (Speech-to-Text) API Keys – Transcription Module
    # ------------------------------------------------------------------
    WHISPER_API_KEY: str = Field(
        default="", description="OpenAI API key used for Whisper transcription."
    )
    DEEPGRAM_API_KEY: str = Field(
        default="", description="Deepgram API key for diarized transcription."
    )
    ASSEMBLYAI_API_KEY: str = Field(
        default="", description="AssemblyAI API key for async transcription polling."
    )

    # ------------------------------------------------------------------
    # LLM – Summarisation Module (provider-agnostic)
    # Supports any OpenAI-compatible API: OpenAI, OpenRouter, Groq,
    # Mistral, Ollama (local), Together AI, Anyscale, etc.
    # ------------------------------------------------------------------
    LLM_API_KEY: str = Field(
        default="",
        description="API key for the chosen LLM provider.",
    )
    LLM_BASE_URL: str = Field(
        default="https://api.openai.com/v1",
        description=(
            "Base URL of the OpenAI-compatible LLM API. "
            "Change this to switch providers without touching any code. "
            "Examples: https://openrouter.ai/api/v1 (OpenRouter), "
            "https://api.groq.com/openai/v1 (Groq), "
            "http://localhost:11434/v1 (Ollama)."
        ),
    )
    LLM_MODEL: str = Field(
        default="gpt-4o",
        description=(
            "Model identifier passed to the provider. "
            "OpenAI: 'gpt-4o'. "
            "OpenRouter: 'openai/gpt-4o' or 'anthropic/claude-3-haiku'. "
            "Groq: 'llama3-70b-8192'. "
            "Ollama: 'llama3'."
        ),
    )
    LLM_TIMEOUT: int = Field(
        default=120,
        description="Maximum seconds to wait for an LLM response before raising LLMTimeoutError.",
    )

    # ------------------------------------------------------------------
    # Storage & Distribution – Output Storage Module (OS)
    # ------------------------------------------------------------------
    MONGO_URI: str = Field(
        default="mongodb://localhost:27017",
        description=(
            "MongoDB connection URI used by the Beanie ODM. "
            "Local default: mongodb://localhost:27017. "
            "Atlas example: mongodb+srv://<user>:<pwd>@<cluster>.mongodb.net/<db>."
        ),
    )
    MONGO_DB: str = Field(
        default="ai_summarizer",
        description="MongoDB database name for the meeting documents.",
    )

    # SMTP credentials for outbound email dispatch (aiosmtplib).
    # Maps to EMAIL_SENDER / EMAIL_PASSWORD in the .env file.
    EMAIL_SENDER: str = Field(
        default="",
        description=(
            "SMTP origin address used by OutputStorage.send_email(). "
            "Example: azmyfahd66@gmail.com"
        ),
    )
    EMAIL_PASSWORD: str = Field(
        default="",
        description=(
            "SMTP authentication credential (app-password or plain password). "
            "For Gmail, generate a 16-character App Password in your Google Account."
        ),
    )
    EMAIL_SMTP_HOST: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname. Default: smtp.gmail.com.",
    )
    EMAIL_SMTP_PORT: int = Field(
        default=587,
        description="SMTP server port (STARTTLS). Default: 587.",
    )

    # ------------------------------------------------------------------
    # Pydantic-settings configuration
    # ------------------------------------------------------------------
    model_config = {
        "env_file": os.path.join(os.path.dirname(__file__), "..", ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
