"""
tests/unit/test_trigger_endpoint.py
------------------------------------
Pytest test suite for the ``POST /api/trigger`` endpoint (T016 / T017).

Design contract
---------------
* Tests use FastAPI's ``TestClient`` with a **minimal app stub** that
  includes only the ``api_router``.  This avoids pulling in the real
  ``src.main`` which requires a fully-populated ``.env`` file and a live
  MongoDB connection.
* ``run_pipeline`` is **always patched** at the ``src.orchestrator`` module
  level so the lazy import inside the endpoint picks up the mock.
* The focus is on verifying:
  1. The endpoint returns HTTP 202 with the correct response shape.
  2. ``BackgroundTasks`` dispatches ``run_pipeline`` with the correct
     keyword arguments.
  3. Validation rejects malformed requests.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routes.api import api_router


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TRIGGER_URL = "/api/trigger"
MEETING_LINK = "https://meet.google.com/abc-defg-hij"
EMAILS = ["alice@example.com", "bob@example.com"]
STORAGE = "email"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    """Yield a synchronous TestClient wrapping a minimal FastAPI stub.

    Only the ``api_router`` is mounted — no database init, no middleware,
    no Settings validation.
    """
    from src.helpers.db import get_db
    from src.helpers.security import get_current_user

    async def fake_current_user():
        user_id = uuid.uuid4()
        company_id = uuid.uuid4()
        return SimpleNamespace(id=user_id, company_id=company_id, role="hr")

    async def fake_db():
        yield AsyncMock()

    stub_app = FastAPI()
    stub_app.include_router(api_router, prefix="/api")
    stub_app.dependency_overrides[get_current_user] = fake_current_user
    stub_app.dependency_overrides[get_db] = fake_db
    return TestClient(stub_app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# T016: Endpoint registration & response shape
# ---------------------------------------------------------------------------


def test_trigger_returns_202_accepted(client) -> None:
    """``POST /api/trigger`` must respond with HTTP 202 Accepted."""
    mock_fn = AsyncMock()
    with (
        patch("src.orchestrator.run_pipeline", mock_fn),
        patch("src.routes.api.resolve_participants", AsyncMock(return_value=EMAILS)),
    ):
        with patch.dict("src.orchestrator.__dict__", {"run_pipeline": mock_fn}):
            response = client.post(
                TRIGGER_URL,
                json={"meeting_link": MEETING_LINK, "storage": STORAGE},
            )
    assert response.status_code == 202, f"Expected 202 but got {response.status_code}"


def test_trigger_response_body_shape(client) -> None:
    """The response JSON must contain message, meeting_link, and storage."""
    mock_fn = AsyncMock()
    with (
        patch("src.orchestrator.run_pipeline", mock_fn),
        patch("src.routes.api.resolve_participants", AsyncMock(return_value=EMAILS)),
    ):
        response = client.post(
            TRIGGER_URL,
            json={"meeting_link": MEETING_LINK, "storage": STORAGE},
        )
    body = response.json()
    assert "message" in body
    assert "session_id" in body
    assert body["meeting_link"] == MEETING_LINK
    assert body["storage"] == STORAGE


def test_trigger_defaults_storage_to_email(client) -> None:
    """When ``storage`` is omitted, it should default to ``'email'``."""
    mock_fn = AsyncMock()
    with (
        patch("src.orchestrator.run_pipeline", mock_fn),
        patch("src.routes.api.resolve_participants", AsyncMock(return_value=[])),
    ):
        response = client.post(
            TRIGGER_URL,
            json={"meeting_link": MEETING_LINK},
        )
    assert response.status_code == 202
    assert response.json()["storage"] == "email"


def test_trigger_rejects_missing_meeting_link(client) -> None:
    """A request without ``meeting_link`` must be rejected with 422."""
    response = client.post(TRIGGER_URL, json={"team_ids": []})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# T017: BackgroundTasks integration — run_pipeline is dispatched correctly
# ---------------------------------------------------------------------------


def test_trigger_dispatches_run_pipeline_with_correct_args(client) -> None:
    """``BackgroundTasks`` must forward the request parameters to
    ``run_pipeline`` as keyword arguments.

    FastAPI's ``TestClient`` executes background tasks **synchronously**
    after the response is returned, so by the time we inspect the mock
    it will have been called.
    """
    mock_fn = AsyncMock()
    with (
        patch("src.orchestrator.run_pipeline", mock_fn),
        patch("src.routes.api.resolve_participants", AsyncMock(return_value=EMAILS)),
    ):
        response = client.post(
            TRIGGER_URL,
            json={
                "meeting_link": MEETING_LINK,
                "team_ids": [],
                "storage": STORAGE,
            },
        )

    assert response.status_code == 202

    from unittest.mock import ANY

    mock_fn.assert_called_once_with(
        meeting_link=MEETING_LINK,
        emails=EMAILS,
        storage=STORAGE,
        session_id=ANY,
        title=None,
        team_ids=[],
        member_ids=[],
        company_id=ANY,
        created_by=ANY,
    )
