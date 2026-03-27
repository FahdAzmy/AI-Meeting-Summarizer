"""
config/settings.py
------------------
Centralised environment-variable configuration for the AI Meeting Summarizer
pipeline.

Sections
--------
  - OBS / Audio Capture  : AC-specific WebSocket credentials & output path
  - (extend here for other modules as needed)

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
    OBS_HOST: str = Field(default="localhost", description="OBS WebSocket server hostname.")
    OBS_PORT: int = Field(default=4455, description="OBS WebSocket server port.")
    OBS_PASSWORD: str = Field(default="", description="OBS WebSocket authentication password.")

    # Directory where OBS will save the raw recordings.
    # Defaults to <project_root>/recordings/
    RECORDINGS_DIR: str = Field(
        default=str(Path(__file__).resolve().parent.parent / "recordings"),
        description="Absolute path to the directory that stores audio recordings.",
    )

    # ------------------------------------------------------------------
    # Pydantic-settings configuration
    # ------------------------------------------------------------------
    model_config = {
        "env_file": os.path.join(os.path.dirname(__file__), "..", ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
