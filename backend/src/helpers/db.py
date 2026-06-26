"""
src/helpers/db.py
-----------------
PostgreSQL-only database connection layer (SQLAlchemy 2.x async).

All MongoDB/ODM drivers and related configuration code have been removed.
"""

import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.helpers.config import settings

logger = logging.getLogger("app")

# Module-level engine and session factory
postgres_engine = None
SessionLocal = None


async def init_db() -> None:
    """Initialize the async PostgreSQL engine and create all tables."""
    global postgres_engine, SessionLocal

    logger.info("Initializing PostgreSQL connection …")

    db_url = settings.get_database_url()
    # Guarantee asyncpg driver prefix
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    postgres_engine = create_async_engine(db_url, echo=False, future=True)
    SessionLocal = async_sessionmaker(
        bind=postgres_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Import all models so their metadata is registered before create_all
    from src.models.base import Base  # noqa: F401 — registers all models via __init__
    import src.models  # noqa: F401

    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env != "production":
        async with postgres_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL connection established and tables auto-created (dev mode)")
    else:
        logger.info(
            "PostgreSQL connection established (production mode — "
            "use 'alembic upgrade head' for schema migrations)"
        )


async def get_db():
    """FastAPI dependency that yields an AsyncSession."""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
