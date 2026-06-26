# tests/unit/test_alembic.py
"""T10.08 — Alembic Migration tests."""
import subprocess
import sys


def test_alembic_heads():
    """Should have exactly one migration head (no branching)."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"], capture_output=True, text=True, cwd="."
    )
    heads = [line for line in result.stdout.strip().split("\n") if line.strip()]
    assert len(heads) == 1


def test_alembic_upgrade_succeeds(test_db_url):
    """alembic upgrade head should apply all migrations without error."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], capture_output=True, text=True, cwd="."
    )
    assert result.returncode == 0
