"""
tests/unit/test_zoom_route.py
-----------------------------
Unit tests for the Zoom signature endpoint (src/routes/zoom.py).

Coverage
--------
- 200 OK: valid request, correct response shape, secret not in response.
- 500 Error: missing CLIENT_ID, missing CLIENT_SECRET, both missing.
- Input validation: missing required field, invalid role values.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import jwt
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.routes.zoom import zoom_router

# ---------------------------------------------------------------------------
# Test application fixture
# ---------------------------------------------------------------------------

app = FastAPI()
app.include_router(zoom_router, prefix="/api")

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_VALID_PAYLOAD = {"meeting_number": "1234567890", "role": 0}
_FAKE_ID = "fake_client_id_abc"
_FAKE_SECRET = "fake_client_secret_xyz"


def _mock_config(client_id: str = _FAKE_ID, client_secret: str = _FAKE_SECRET):
    """Return a mock Config object with controllable Zoom credentials."""
    cfg = MagicMock()
    cfg.ZOOM_SDK_CLIENT_ID = client_id
    cfg.ZOOM_SDK_CLIENT_SECRET = client_secret
    return cfg


# ===========================================================================
# Success cases
# ===========================================================================


class TestZoomSignatureSuccess:
    """Tests for the happy-path of POST /api/zoom/signature."""

    def test_returns_200_with_valid_payload(self):
        """Valid request with configured credentials returns HTTP 200."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post("/api/zoom/signature", json=_VALID_PAYLOAD)
        assert response.status_code == 200

    def test_response_contains_signature_field(self):
        """Response body must include a non-empty 'signature' string."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post("/api/zoom/signature", json=_VALID_PAYLOAD)
        data = response.json()
        assert "signature" in data
        assert isinstance(data["signature"], str)
        assert len(data["signature"]) > 0

    def test_response_contains_sdk_key_field(self):
        """Response body must include the CLIENT_ID as 'sdk_key'."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post("/api/zoom/signature", json=_VALID_PAYLOAD)
        data = response.json()
        assert data["sdk_key"] == _FAKE_ID

    def test_response_does_not_contain_secret(self):
        """The CLIENT_SECRET must never appear in the response body."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post("/api/zoom/signature", json=_VALID_PAYLOAD)
        assert _FAKE_SECRET not in response.text

    def test_signature_is_valid_jwt(self):
        """The 'signature' field must be a decodable HS256 JWT."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post("/api/zoom/signature", json=_VALID_PAYLOAD)
        token = response.json()["signature"]
        payload = jwt.decode(token, _FAKE_SECRET, algorithms=["HS256"])
        assert payload["mn"] == "1234567890"

    def test_jwt_role_is_attendee(self):
        """JWT payload must reflect role=0 (attendee) from request."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post("/api/zoom/signature", json={**_VALID_PAYLOAD, "role": 0})
        token = response.json()["signature"]
        payload = jwt.decode(token, _FAKE_SECRET, algorithms=["HS256"])
        assert payload["role"] == 0

    def test_jwt_role_is_host(self):
        """JWT payload must reflect role=1 (host) from request."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post("/api/zoom/signature", json={**_VALID_PAYLOAD, "role": 1})
        token = response.json()["signature"]
        payload = jwt.decode(token, _FAKE_SECRET, algorithms=["HS256"])
        assert payload["role"] == 1

    def test_role_defaults_to_attendee_when_omitted(self):
        """When role is omitted, the endpoint defaults to 0 (attendee)."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post("/api/zoom/signature", json={"meeting_number": "1234567890"})
        assert response.status_code == 200
        token = response.json()["signature"]
        payload = jwt.decode(token, _FAKE_SECRET, algorithms=["HS256"])
        assert payload["role"] == 0


# ===========================================================================
# Error cases — missing credentials
# ===========================================================================


class TestZoomSignatureMissingCredentials:
    """Tests for HTTP 500 when Zoom SDK credentials are not configured."""

    def test_returns_500_when_client_id_missing(self):
        """HTTP 500 when ZOOM_SDK_CLIENT_ID is empty."""
        with patch("src.routes.zoom.Config", return_value=_mock_config(client_id="")):
            response = client.post("/api/zoom/signature", json=_VALID_PAYLOAD)
        assert response.status_code == 500

    def test_returns_500_when_client_secret_missing(self):
        """HTTP 500 when ZOOM_SDK_CLIENT_SECRET is empty."""
        with patch("src.routes.zoom.Config", return_value=_mock_config(client_secret="")):
            response = client.post("/api/zoom/signature", json=_VALID_PAYLOAD)
        assert response.status_code == 500

    def test_returns_500_when_both_credentials_missing(self):
        """HTTP 500 when both ZOOM_SDK credentials are empty."""
        with patch("src.routes.zoom.Config", return_value=_mock_config("", "")):
            response = client.post("/api/zoom/signature", json=_VALID_PAYLOAD)
        assert response.status_code == 500

    def test_500_detail_message(self):
        """Error detail must indicate credentials are not configured."""
        with patch("src.routes.zoom.Config", return_value=_mock_config("", "")):
            response = client.post("/api/zoom/signature", json=_VALID_PAYLOAD)
        assert "credentials not configured" in response.json()["detail"].lower()


# ===========================================================================
# Input validation
# ===========================================================================


class TestZoomSignatureInputValidation:
    """Tests for Pydantic request validation."""

    def test_returns_422_when_meeting_number_missing(self):
        """HTTP 422 when 'meeting_number' is absent from the request body."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post("/api/zoom/signature", json={"role": 0})
        assert response.status_code == 422

    def test_returns_422_when_role_out_of_range(self):
        """HTTP 422 when 'role' is not 0 or 1."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post(
                "/api/zoom/signature",
                json={"meeting_number": "1234567890", "role": 2},
            )
        assert response.status_code == 422

    def test_returns_422_when_role_negative(self):
        """HTTP 422 when 'role' is negative."""
        with patch("src.routes.zoom.Config", return_value=_mock_config()):
            response = client.post(
                "/api/zoom/signature",
                json={"meeting_number": "1234567890", "role": -1},
            )
        assert response.status_code == 422
