"""
alembic/env.py
--------------
Async-capable Alembic environment for SQLAlchemy 2.x + asyncpg.

Uses asyncio runner so migrations run against the same async engine
as the application, ensuring 100% schema parity.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool

from alembic import context

# ── Alembic config object ─────────────────────────────────────────────────────
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import all models so their tables appear in metadata ──────────────────────
# This import must happen BEFORE target_metadata is set.
import src.models  # noqa: F401 — side-effect: registers all ORM models
from src.models.base import Base

target_metadata = Base.metadata


# ── URL helper ────────────────────────────────────────────────────────────────
def get_url() -> str:
    """Prefer the DATABASE_URL env-var over the .ini value."""
    import os
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url", "")
    # Guarantee asyncpg driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# ── Offline migrations ────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online (async) migrations ─────────────────────────────────────────────────
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations through a sync wrapper."""
    url = get_url()
    connectable = create_async_engine(url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entry point ───────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
