"""
src/helpers/config.py
---------------------
Application settings loaded from environment variables / .env file.
PostgreSQL-only: all MongoDB settings have been removed.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Project root == backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ── PostgreSQL ────────────────────────────────────────────────────────
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_SERVER: str | None = None
    POSTGRES_PORT: str | None = None
    POSTGRES_DB: str | None = None

    # Full connection URL takes precedence over individual fields
    DATABASE_URL: str | None = None
    TEST_DATABASE_URL: str | None = None

    # ── JWT ──────────────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_SECRET_KEY: str
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # ── Email ─────────────────────────────────────────────────────────────
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: str

    def get_database_url(self) -> str:
        """Return the async-ready PostgreSQL connection URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def get_test_database_url(self) -> str:
        """Return the test database URL (required for running the test suite)."""
        if not self.TEST_DATABASE_URL:
            raise RuntimeError("TEST_DATABASE_URL is not set in the environment.")
        return self.TEST_DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://"
        )

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
