"""
tests/unit/test_summarisation.py
---------------------------------
TDD test suite for the Summarisation & Analysis Module.

All OpenAI SDK calls are mocked via ``unittest.mock.patch`` so that:
  - No real API calls are made (zero cost, deterministic).
  - Each test verifies schema parsing, error mapping, and math logic in isolation.

Coverage
--------
  T005  Base pytest setup – patching openai.OpenAI globally.
  T006  generate_report() returns a ``summary`` key with markdown text (US1).
  T007  Action items resolve correctly into Python list-of-dicts (US2).
  T008  Mangled JSON response triggers ParseError (US2).
  T012  Speaker participation math is computed correctly from mock segments (US3).
  T013  Missing diarisation data returns speaker_stats=None (US3).
  T015  Empty transcript raises EmptyTranscriptError immediately (US4).
  T016  OpenAI APITimeoutError maps onto LLMTimeoutError (US4).
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from modules.llm_errors import (
    EmptyTranscriptError,
    LLMTimeoutError,
    ParseError,
)
from modules.summarisation import Summarisation, _analyse_participation


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _make_openai_response(payload: dict) -> MagicMock:
    """Build a minimal mock that mirrors openai ChatCompletion response shape."""
    content = json.dumps(payload)
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


MINIMAL_TRANSCRIPT: dict[str, Any] = {
    "full_text": "Alice: Please finish the report by Friday. Bob: Sure, I will.",
    "segments": [],
    "diarisation_available": False,
    "duration_seconds": 12.0,
}

VALID_LLM_PAYLOAD: dict[str, Any] = {
    "summary": "## Meeting Summary\n\nAlice asked Bob to finish the report by Friday.",
    "action_items": [
        {"assignee": "Bob", "task": "Finish the report", "deadline": "Friday"}
    ],
    "decisions": ["Report deadline set to Friday"],
    "follow_up": ["Confirm report format with Alice"],
}


# ---------------------------------------------------------------------------
# T005 – Base Pytest / mock scaffold
# ---------------------------------------------------------------------------

class TestBaseMockSetup:
    """T005: Verify that openai.OpenAI can be patched and the class instantiates safely."""

    def test_summarisation_instantiates_with_mocked_openai(self):
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_cls.return_value = MagicMock()
            bot = Summarisation()
            assert bot.model is not None
            assert bot.temperature == 0.3

    def test_temperature_locked_at_default(self):
        with patch("modules.summarisation.openai.OpenAI"):
            bot = Summarisation()
            assert bot.temperature == 0.3, "Temperature must default to 0.3 per research.md"

    def test_custom_model_accepted(self):
        with patch("modules.summarisation.openai.OpenAI"):
            bot = Summarisation(model="gpt-3.5-turbo")
            assert bot.model == "gpt-3.5-turbo"


# ---------------------------------------------------------------------------
# T006 – generate_report() summary key (US1)
# ---------------------------------------------------------------------------

class TestGenerateReportSummary:
    """T006: generate_report() must return a dict with a non-empty ``summary`` key."""

    def test_summary_key_exists_in_report(self):
        mock_response = _make_openai_response(VALID_LLM_PAYLOAD)
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            report = bot.generate_report(MINIMAL_TRANSCRIPT)

            assert "summary" in report

    def test_summary_contains_markdown_text(self):
        mock_response = _make_openai_response(VALID_LLM_PAYLOAD)
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            report = bot.generate_report(MINIMAL_TRANSCRIPT)

            assert isinstance(report["summary"], str)
            assert len(report["summary"]) > 0
            # Markdown heading should be preserved
            assert "##" in report["summary"]

    def test_report_contains_all_required_keys(self):
        mock_response = _make_openai_response(VALID_LLM_PAYLOAD)
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            report = bot.generate_report(MINIMAL_TRANSCRIPT)

            for key in ("summary", "action_items", "decisions", "follow_up", "speaker_stats"):
                assert key in report, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# T007 – Action items resolve to Python list-of-dicts (US2)
# ---------------------------------------------------------------------------

class TestActionItemsParsing:
    """T007: Action items from JSON Mode must map cleanly into Python list-of-dicts."""

    def test_action_items_is_a_list(self):
        mock_response = _make_openai_response(VALID_LLM_PAYLOAD)
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            report = bot.generate_report(MINIMAL_TRANSCRIPT)

            assert isinstance(report["action_items"], list)

    def test_action_item_has_required_fields(self):
        mock_response = _make_openai_response(VALID_LLM_PAYLOAD)
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            report = bot.generate_report(MINIMAL_TRANSCRIPT)

            item = report["action_items"][0]
            assert "assignee" in item
            assert "task" in item
            assert "deadline" in item

    def test_action_item_values_match_mock_payload(self):
        mock_response = _make_openai_response(VALID_LLM_PAYLOAD)
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            report = bot.generate_report(MINIMAL_TRANSCRIPT)

            item = report["action_items"][0]
            assert item["assignee"] == "Bob"
            assert item["task"] == "Finish the report"
            assert item["deadline"] == "Friday"

    def test_decisions_and_followup_are_lists_of_strings(self):
        mock_response = _make_openai_response(VALID_LLM_PAYLOAD)
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            report = bot.generate_report(MINIMAL_TRANSCRIPT)

            assert isinstance(report["decisions"], list)
            assert isinstance(report["follow_up"], list)
            assert all(isinstance(d, str) for d in report["decisions"])
            assert all(isinstance(f, str) for f in report["follow_up"])


# ---------------------------------------------------------------------------
# T008 – Mangled JSON triggers ParseError (US2)
# ---------------------------------------------------------------------------

class TestParseErrorBoundary:
    """T008: A malformed / missing-key LLM response must raise ParseError (SM-003)."""

    def test_missing_required_key_raises_parse_error(self):
        """LLM returns JSON that lacks the ``summary`` key → ParseError."""
        broken_payload = {"action_items": [], "decisions": [], "follow_up": []}
        mock_response = _make_openai_response(broken_payload)
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            with pytest.raises(ParseError) as exc_info:
                bot.generate_report(MINIMAL_TRANSCRIPT)

            assert exc_info.value.code == "SM-003"

    def test_invalid_json_string_raises_parse_error(self):
        """LLM returns raw non-JSON text → ParseError."""
        choice = MagicMock()
        choice.message.content = "Sorry, I cannot summarise this."
        response = MagicMock()
        response.choices = [choice]

        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            with pytest.raises(ParseError):
                bot.generate_report(MINIMAL_TRANSCRIPT)

    def test_parse_error_code_is_sm003(self):
        broken_payload = {"foo": "bar"}
        mock_response = _make_openai_response(broken_payload)
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            with pytest.raises(ParseError) as exc_info:
                bot.generate_report(MINIMAL_TRANSCRIPT)

            assert "SM-003" in str(exc_info.value)


# ---------------------------------------------------------------------------
# T012 – Speaker participation math (US3)
# ---------------------------------------------------------------------------

class TestSpeakerParticipationAnalytics:
    """T012: _analyse_participation must correctly compute durations and percentages."""

    MOCK_SEGMENTS = [
        {"speaker": "Speaker 0", "start": 0.0,  "end": 30.0},
        {"speaker": "Speaker 1", "start": 30.0, "end": 50.0},
        {"speaker": "Speaker 0", "start": 50.0, "end": 70.0},
        {"speaker": "Speaker 1", "start": 70.0, "end": 80.0},
    ]

    def test_total_duration_is_correct(self):
        result = _analyse_participation(self.MOCK_SEGMENTS)
        assert result is not None
        # Speaker 0: 30 + 20 = 50s  |  Speaker 1: 20 + 10 = 30s  |  total = 80s
        assert result["total_meeting_duration_sec"] == pytest.approx(80.0)

    def test_speaker_speaking_times_are_correct(self):
        result = _analyse_participation(self.MOCK_SEGMENTS)
        assert result is not None
        times = {s["speaker"]: s["total_speaking_time_sec"] for s in result["speakers"]}
        assert times["Speaker 0"] == pytest.approx(50.0)
        assert times["Speaker 1"] == pytest.approx(30.0)

    def test_percentages_sum_to_100(self):
        result = _analyse_participation(self.MOCK_SEGMENTS)
        assert result is not None
        total_pct = sum(s["percentage_of_meeting"] for s in result["speakers"])
        assert total_pct == pytest.approx(100.0, abs=0.1)

    def test_most_active_speaker_identified(self):
        result = _analyse_participation(self.MOCK_SEGMENTS)
        assert result is not None
        assert result["most_active_speaker"] == "Speaker 0"

    def test_number_of_turns_counted_correctly(self):
        result = _analyse_participation(self.MOCK_SEGMENTS)
        assert result is not None
        turns = {s["speaker"]: s["number_of_turns"] for s in result["speakers"]}
        assert turns["Speaker 0"] == 2
        assert turns["Speaker 1"] == 2

    def test_generate_report_includes_speaker_stats_when_diarised(self):
        mock_response = _make_openai_response(VALID_LLM_PAYLOAD)
        transcript = {
            "full_text": "Some text.",
            "segments": self.MOCK_SEGMENTS,
            "diarisation_available": True,
            "duration_seconds": 80.0,
        }
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            report = bot.generate_report(transcript)

            assert report["speaker_stats"] is not None
            assert "speakers" in report["speaker_stats"]
            assert "most_active_speaker" in report["speaker_stats"]


# ---------------------------------------------------------------------------
# T013 – Missing diarisation → speaker_stats=None (US3)
# ---------------------------------------------------------------------------

class TestNoDiarisationData:
    """T013: When diarisation is unavailable or segments are empty, speaker_stats must be None."""

    def test_analyse_participation_returns_none_for_empty_segments(self):
        result = _analyse_participation([])
        assert result is None

    def test_analyse_participation_returns_none_when_no_speaker_labels(self):
        segments_without_speakers = [
            {"start": 0.0, "end": 10.0},    # no "speaker" key
            {"start": 10.0, "end": 20.0},
        ]
        result = _analyse_participation(segments_without_speakers)
        assert result is None

    def test_generate_report_speaker_stats_none_when_diarisation_false(self):
        mock_response = _make_openai_response(VALID_LLM_PAYLOAD)
        transcript = {
            "full_text": "Some text.",
            "segments": [],
            "diarisation_available": False,
            "duration_seconds": 20.0,
        }
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_cls.return_value = mock_client

            bot = Summarisation()
            report = bot.generate_report(transcript)

            assert report["speaker_stats"] is None


# ---------------------------------------------------------------------------
# T015 – Empty transcript raises EmptyTranscriptError (US4)
# ---------------------------------------------------------------------------

class TestEmptyTranscriptGuard:
    """T015: A zero-byte / empty full_text must trigger EmptyTranscriptError before any API call."""

    def test_empty_full_text_raises_empty_transcript_error(self):
        transcript = {
            "full_text": "",
            "segments": [],
            "diarisation_available": False,
            "duration_seconds": 0.0,
        }
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            bot = Summarisation()
            with pytest.raises(EmptyTranscriptError) as exc_info:
                bot.generate_report(transcript)

            assert exc_info.value.code == "SM-004"
            # Critically: no API call should have been made
            mock_client.chat.completions.create.assert_not_called()

    def test_whitespace_only_transcript_raises_empty_transcript_error(self):
        transcript = {
            "full_text": "   \n\t  ",
            "segments": [],
            "diarisation_available": False,
            "duration_seconds": 0.0,
        }
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            bot = Summarisation()
            with pytest.raises(EmptyTranscriptError):
                bot.generate_report(transcript)

    def test_missing_full_text_key_raises_empty_transcript_error(self):
        transcript = {
            "segments": [],
            "diarisation_available": False,
            "duration_seconds": 0.0,
        }
        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client

            bot = Summarisation()
            with pytest.raises(EmptyTranscriptError):
                bot.generate_report(transcript)

    def test_empty_transcript_error_code_is_sm004(self):
        transcript = {"full_text": ""}
        with patch("modules.summarisation.openai.OpenAI"):
            bot = Summarisation()
            with pytest.raises(EmptyTranscriptError) as exc_info:
                bot.generate_report(transcript)

            assert "SM-004" in str(exc_info.value)


# ---------------------------------------------------------------------------
# T016 – APITimeoutError maps to LLMTimeoutError (US4)
# ---------------------------------------------------------------------------

class TestTimeoutMapping:
    """T016: openai.APITimeoutError from the mock must be re-raised as LLMTimeoutError (SM-002)."""

    def test_api_timeout_raises_llm_timeout_error(self):
        import openai as _openai

        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = _openai.APITimeoutError(
                request=MagicMock()
            )
            mock_cls.return_value = mock_client

            bot = Summarisation()
            with pytest.raises(LLMTimeoutError) as exc_info:
                bot.generate_report(MINIMAL_TRANSCRIPT)

            assert exc_info.value.code == "SM-002"

    def test_llm_timeout_error_code_is_sm002(self):
        import openai as _openai

        with patch("modules.summarisation.openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = _openai.APITimeoutError(
                request=MagicMock()
            )
            mock_cls.return_value = mock_client

            bot = Summarisation()
            with pytest.raises(LLMTimeoutError) as exc_info:
                bot.generate_report(MINIMAL_TRANSCRIPT)

            assert "SM-002" in str(exc_info.value)
