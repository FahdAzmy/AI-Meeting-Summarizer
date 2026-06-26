"""
tests/unit/test_zoom_sdk.py
---------------------------
Unit tests for the Zoom SDK helper utilities (src/helpers/zoom_sdk.py).

Coverage
--------
- URL parsing: valid URLs, URLs with passcode, company-subdomain URLs,
  invalid / non-Zoom URLs, edge cases.
- JWT generation: correct payload shape, algorithm, credential validation.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import jwt
import pytest

from src.helpers.zoom_sdk import (
    ZoomMeetingDetails,
    generate_zoom_signature,
    parse_zoom_url,
)


# ===========================================================================
# parse_zoom_url — User Story 3
# ===========================================================================


class TestParseZoomUrl:
    """Tests for parse_zoom_url()."""

    def test_standard_url_without_passcode(self):
        """Standard zoom.us/j/{id} URL — no passcode."""
        result = parse_zoom_url("https://zoom.us/j/1234567890")
        assert result is not None
        assert result["meeting_number"] == "1234567890"
        assert result["passcode"] == ""

    def test_standard_url_with_passcode(self):
        """Standard URL with ?pwd= query parameter."""
        result = parse_zoom_url("https://zoom.us/j/1234567890?pwd=abc123")
        assert result is not None
        assert result["meeting_number"] == "1234567890"
        assert result["passcode"] == "abc123"

    def test_company_subdomain_without_passcode(self):
        """Company-vanity subdomain URL without passcode."""
        result = parse_zoom_url("https://acme.zoom.us/j/9876543210")
        assert result is not None
        assert result["meeting_number"] == "9876543210"
        assert result["passcode"] == ""

    def test_company_subdomain_with_passcode(self):
        """Company-vanity subdomain URL with passcode."""
        result = parse_zoom_url("https://acme.zoom.us/j/9876543210?pwd=XyZ789")
        assert result is not None
        assert result["meeting_number"] == "9876543210"
        assert result["passcode"] == "XyZ789"

    def test_http_url(self):
        """http:// (non-HTTPS) Zoom URLs are also matched."""
        result = parse_zoom_url("http://zoom.us/j/1111111111")
        assert result is not None
        assert result["meeting_number"] == "1111111111"

    def test_url_with_alphanumeric_passcode(self):
        """Passcode containing mixed alphanumeric characters."""
        result = parse_zoom_url("https://zoom.us/j/5555555555?pwd=AbCdEf123")
        assert result is not None
        assert result["passcode"] == "AbCdEf123"

    def test_non_zoom_url_returns_none(self):
        """Non-Zoom URLs must return None."""
        assert parse_zoom_url("https://meet.google.com/abc-defg-hij") is None

    def test_teams_url_returns_none(self):
        """Microsoft Teams URLs must return None."""
        assert parse_zoom_url("https://teams.microsoft.com/l/meetup-join/abc") is None

    def test_empty_string_returns_none(self):
        """Empty string must return None."""
        assert parse_zoom_url("") is None

    def test_plain_text_returns_none(self):
        """Arbitrary text (not a URL) must return None."""
        assert parse_zoom_url("not a url at all") is None

    def test_zoom_homepage_returns_none(self):
        """zoom.us without a /j/ path returns None."""
        assert parse_zoom_url("https://zoom.us/") is None

    def test_returns_correct_typed_dict_shape(self):
        """Result is a dict with exactly the expected keys."""
        result = parse_zoom_url("https://zoom.us/j/1234567890?pwd=test")
        assert isinstance(result, dict)
        assert set(result.keys()) == {"meeting_number", "passcode"}

    def test_long_meeting_id(self):
        """11-digit meeting IDs (Zoom's maximum) are parsed correctly."""
        result = parse_zoom_url("https://zoom.us/j/12345678901")
        assert result is not None
        assert result["meeting_number"] == "12345678901"


# ===========================================================================
# generate_zoom_signature — User Story 5
# ===========================================================================


class TestGenerateZoomSignature:
    """Tests for generate_zoom_signature()."""

    _SDK_KEY = "test_client_id"
    _SDK_SECRET = "test_client_secret"

    def test_returns_string(self):
        """The function must return a non-empty string."""
        token = generate_zoom_signature("1234567890", 0, self._SDK_KEY, self._SDK_SECRET)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_is_decodable_jwt(self):
        """The returned token must be a valid JWT decodable with the secret."""
        token = generate_zoom_signature("1234567890", 0, self._SDK_KEY, self._SDK_SECRET)
        payload = jwt.decode(token, self._SDK_SECRET, algorithms=["HS256"])
        assert payload is not None

    def test_payload_contains_meeting_number(self):
        """JWT payload must include the meeting number as 'mn'."""
        token = generate_zoom_signature("9876543210", 0, self._SDK_KEY, self._SDK_SECRET)
        payload = jwt.decode(token, self._SDK_SECRET, algorithms=["HS256"])
        assert payload["mn"] == "9876543210"

    def test_payload_contains_role(self):
        """JWT payload must include the requested role (0 = attendee)."""
        token = generate_zoom_signature("1234567890", 0, self._SDK_KEY, self._SDK_SECRET)
        payload = jwt.decode(token, self._SDK_SECRET, algorithms=["HS256"])
        assert payload["role"] == 0

    def test_payload_host_role(self):
        """JWT payload must include role = 1 for host requests."""
        token = generate_zoom_signature("1234567890", 1, self._SDK_KEY, self._SDK_SECRET)
        payload = jwt.decode(token, self._SDK_SECRET, algorithms=["HS256"])
        assert payload["role"] == 1

    def test_payload_contains_sdk_key(self):
        """JWT payload must embed the sdk_key as 'sdkKey' and 'appKey'."""
        token = generate_zoom_signature("1234567890", 0, self._SDK_KEY, self._SDK_SECRET)
        payload = jwt.decode(token, self._SDK_SECRET, algorithms=["HS256"])
        assert payload["sdkKey"] == self._SDK_KEY
        assert payload["appKey"] == self._SDK_KEY

    def test_payload_secret_not_in_token(self):
        """The sdk_secret must NOT appear anywhere in the raw JWT string."""
        token = generate_zoom_signature("1234567890", 0, self._SDK_KEY, self._SDK_SECRET)
        assert self._SDK_SECRET not in token

    def test_token_expires_in_two_hours(self):
        """The JWT must expire approximately 7200 seconds from now."""
        before = int(time.time())
        token = generate_zoom_signature("1234567890", 0, self._SDK_KEY, self._SDK_SECRET)
        after = int(time.time())
        payload = jwt.decode(token, self._SDK_SECRET, algorithms=["HS256"])
        assert before + 7200 <= payload["exp"] <= after + 7200

    def test_algorithm_is_hs256(self):
        """The JWT must use the HS256 algorithm (per Zoom documentation)."""
        token = generate_zoom_signature("1234567890", 0, self._SDK_KEY, self._SDK_SECRET)
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "HS256"

    def test_raises_if_sdk_key_empty(self):
        """ValueError raised when sdk_key is an empty string."""
        with pytest.raises(ValueError, match="ZOOM_SDK_CLIENT_ID"):
            generate_zoom_signature("1234567890", 0, "", self._SDK_SECRET)

    def test_raises_if_sdk_secret_empty(self):
        """ValueError raised when sdk_secret is an empty string."""
        with pytest.raises(ValueError, match="ZOOM_SDK_CLIENT_SECRET"):
            generate_zoom_signature("1234567890", 0, self._SDK_KEY, "")

    def test_different_meeting_numbers_produce_different_tokens(self):
        """Distinct meeting numbers must produce distinct JWT tokens."""
        token_a = generate_zoom_signature("1111111111", 0, self._SDK_KEY, self._SDK_SECRET)
        token_b = generate_zoom_signature("2222222222", 0, self._SDK_KEY, self._SDK_SECRET)
        assert token_a != token_b
