# tests/unit/test_db_connection.py
"""T10.01 — Database Connection tests."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_init_db_creates_engine(test_db):
    """init_db() should create a valid async engine and session factory."""
    from src.helpers.db import postgres_engine, SessionLocal
    assert postgres_engine is not None
    assert SessionLocal is not None


@pytest.mark.asyncio
async def test_get_db_yields_session(test_db):
    """get_db() dependency should yield an AsyncSession."""
    from src.helpers.db import get_db
    async for session in get_db():
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_no_mongodb_imports():
    """Ensure no MongoDB dependencies are imported anywhere in db.py."""
    import inspect
    from src.helpers import db
    source = inspect.getsource(db)
    assert "motor" not in source
    assert "beanie" not in source
    assert "AsyncIOMotorClient" not in source
