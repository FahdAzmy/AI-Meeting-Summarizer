"""
tests/unit/test_transcription.py
---------------------------------
TDD test suite for the Transcription Module.

Design rules
------------
- NO live API calls.  All external I/O is intercepted via unittest.mock /
  pytest monkeypatch.
- Each test focuses on a single behaviour so failures are trivially diagnosable.
- Fixtures provide isolated, credential-free Transcription instances.

Coverage map
------------
  T005  – base fixtures / isolated env
  T006  – _transcribe_whisper (mock OpenAI SDK)
  T007  – _transcribe_deepgram (mock requests.post)
  T008  – _transcribe_assemblyai (mock assemblyai SDK)
  T009  – _normalise for all three providers
  T014  – HTTP 408 retry loop → STTTimeoutError
  T015  – HTTP 429 triggers provider fallback
  T016  – HTTP 401 causes instant STTProviderError (no backoff)
  T019  – file > 25 MB triggers AudioTooLargeError
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Guard: make sure the module can be imported without real credentials
# ---------------------------------------------------------------------------

os.environ.setdefault("WHISPER_API_KEY", "test-whisper-key")
os.environ.setdefault("DEEPGRAM_API_KEY", "test-deepgram-key")
os.environ.setdefault("ASSEMBLYAI_API_KEY", "test-assemblyai-key")

from modules.stt_errors import (  # noqa: E402
    AudioTooLargeError,
    NormalisationError,
    STTProviderError,
    STTRateLimitError,
    STTTimeoutError,
)
from modules.transcription import Transcription  # noqa: E402

# ---------------------------------------------------------------------------
# T005 – Base fixtures
# ---------------------------------------------------------------------------

DUMMY_AUDIO = "/tmp/meeting.wav"
_25MB_PLUS_1 = 25 * 1024 * 1024 + 1


@pytest.fixture()
def whisper_bot() -> Transcription:
    """Isolated Transcription instance using Whisper provider."""
    return Transcription(provider="whisper")


@pytest.fixture()
def deepgram_bot() -> Transcription:
    """Isolated Transcription instance using Deepgram provider."""
    return Transcription(provider="deepgram")


@pytest.fixture()
def assemblyai_bot() -> Transcription:
    """Isolated Transcription instance using AssemblyAI provider."""
    return Transcription(provider="assemblyai")


# ── Raw mock payloads ────────────────────────────────────────────────────────

WHISPER_RAW: dict[str, Any] = {
    "_provider": "whisper",
    "text": "Hello world. This is a test.",
    "segments": [
        {"start": 0.0, "end": 2.5, "text": "Hello world."},
        {"start": 2.5, "end": 5.0, "text": "This is a test."},
    ],
    "language": "en",
    "duration": 5.0,
}

DEEPGRAM_RAW: dict[str, Any] = {
    "_provider": "deepgram",
    "metadata": {"duration": 6.0, "language": "en"},
    "results": {
        "channels": [
            {
                "alternatives": [
                    {
                        "transcript": "Hello. Who are you?",
                        "words": [
                            {"word": "Hello", "punctuated_word": "Hello.", "start": 0.0, "end": 0.5, "speaker": 0},
                            {"word": "Who", "punctuated_word": "Who", "start": 1.0, "end": 1.3, "speaker": 1},
                            {"word": "are", "punctuated_word": "are", "start": 1.3, "end": 1.5, "speaker": 1},
                            {"word": "you", "punctuated_word": "you?", "start": 1.5, "end": 1.8, "speaker": 1},
                        ],
                    }
                ]
            }
        ]
    },
}

ASSEMBLYAI_RAW: dict[str, Any] = {
    "_provider": "assemblyai",
    "text": "Good morning team.",
    "utterances": [
        {"speaker": "A", "start": 0, "end": 2000, "text": "Good morning team."},
    ],
    "language_code": "en",
    "audio_duration": 2.0,
}


# ---------------------------------------------------------------------------
# T006 – _transcribe_whisper mocked via OpenAI SDK
# ---------------------------------------------------------------------------

class TestTranscribeWhisper:
    """T006 – Unit tests for _transcribe_whisper."""

    def _make_sdk_response(self) -> MagicMock:
        """Return a mock that mimics the OpenAI SDK Transcription object."""
        mock_seg = MagicMock()
        mock_seg.start = 0.0
        mock_seg.end = 2.5
        mock_seg.text = "Hello world."

        resp = MagicMock()
        resp.text = "Hello world."
        resp.segments = [mock_seg]
        resp.language = "en"
        resp.duration = 5.0
        return resp

    @patch("modules.transcription.openai")
    def test_whisper_returns_raw_dict(self, mock_openai: MagicMock, whisper_bot: Transcription) -> None:
        """Successful Whisper call returns a dict with _provider=='whisper'."""
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = self._make_sdk_response()

        with patch("builtins.open", MagicMock()):
            raw = whisper_bot._transcribe_whisper(DUMMY_AUDIO)

        assert raw["_provider"] == "whisper"
        assert raw["text"] == "Hello world."
        assert isinstance(raw["segments"], list)

    @patch("modules.transcription.openai.OpenAI")
    def test_whisper_408_raises_timeout(self, mock_openai_cls: MagicMock, whisper_bot: Transcription) -> None:
        """HTTP 408 from Whisper raises STTTimeoutError."""
        import openai as real_openai

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Build a real openai.APIStatusError (needs response + body kwargs)
        fake_response = MagicMock()
        fake_response.status_code = 408
        fake_response.headers = {}
        err = real_openai.APIStatusError(
            message="Request Timeout",
            response=fake_response,
            body={},
        )
        mock_client.audio.transcriptions.create.side_effect = err

        with patch("builtins.open", MagicMock()):
            with pytest.raises(STTTimeoutError):
                whisper_bot._transcribe_whisper(DUMMY_AUDIO)

    @patch("modules.transcription.openai.OpenAI")
    def test_whisper_429_raises_rate_limit(self, mock_openai_cls: MagicMock, whisper_bot: Transcription) -> None:
        """HTTP 429 from Whisper raises STTRateLimitError."""
        import openai as real_openai

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        fake_response = MagicMock()
        fake_response.status_code = 429
        fake_response.headers = {}
        err = real_openai.APIStatusError(
            message="Rate limit exceeded",
            response=fake_response,
            body={},
        )
        mock_client.audio.transcriptions.create.side_effect = err

        with patch("builtins.open", MagicMock()):
            with pytest.raises(STTRateLimitError):
                whisper_bot._transcribe_whisper(DUMMY_AUDIO)


# ---------------------------------------------------------------------------
# T007 – _transcribe_deepgram mocked via requests.post
# ---------------------------------------------------------------------------

class TestTranscribeDeepgram:
    """T007 – Unit tests for _transcribe_deepgram."""

    @patch("modules.transcription.requests.post")
    def test_deepgram_returns_raw_dict(self, mock_post: MagicMock, deepgram_bot: Transcription) -> None:
        """Successful Deepgram call returns response JSON with _provider=='deepgram'."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = dict(DEEPGRAM_RAW)
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        with patch("builtins.open", MagicMock()):
            raw = deepgram_bot._transcribe_deepgram(DUMMY_AUDIO)

        assert raw["_provider"] == "deepgram"
        assert "results" in raw
        # Verify diarize=true is in the URL
        call_url = mock_post.call_args[0][0]
        assert "diarize=true" in call_url

    @patch("modules.transcription.requests.post")
    def test_deepgram_408_raises_timeout(self, mock_post: MagicMock, deepgram_bot: Transcription) -> None:
        """HTTP 408 response raises STTTimeoutError."""
        import requests as req_lib

        mock_resp = MagicMock()
        mock_resp.status_code = 408
        http_err = req_lib.exceptions.HTTPError(response=mock_resp)
        mock_post.return_value = mock_resp
        mock_resp.raise_for_status.side_effect = http_err

        with patch("builtins.open", MagicMock()):
            with pytest.raises(STTTimeoutError):
                deepgram_bot._transcribe_deepgram(DUMMY_AUDIO)

    @patch("modules.transcription.requests.post")
    def test_deepgram_429_raises_rate_limit(self, mock_post: MagicMock, deepgram_bot: Transcription) -> None:
        """HTTP 429 response raises STTRateLimitError."""
        import requests as req_lib

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        http_err = req_lib.exceptions.HTTPError(response=mock_resp)
        mock_post.return_value = mock_resp
        mock_resp.raise_for_status.side_effect = http_err

        with patch("builtins.open", MagicMock()):
            with pytest.raises(STTRateLimitError):
                deepgram_bot._transcribe_deepgram(DUMMY_AUDIO)


# ---------------------------------------------------------------------------
# T008 – _transcribe_assemblyai mocked via assemblyai SDK
# ---------------------------------------------------------------------------

class TestTranscribeAssemblyAI:
    """T008 – Unit tests for _transcribe_assemblyai."""

    @patch("modules.transcription.aai")
    def test_assemblyai_returns_raw_dict(self, mock_aai: MagicMock, assemblyai_bot: Transcription) -> None:
        """Successful AssemblyAI call returns dict with _provider=='assemblyai'."""
        mock_utterance = MagicMock()
        mock_utterance.speaker = "A"
        mock_utterance.start = 0
        mock_utterance.end = 2000
        mock_utterance.text = "Good morning team."

        mock_transcript = MagicMock()
        mock_transcript.status = MagicMock()
        mock_transcript.status.__eq__ = lambda s, o: False  # not error
        mock_transcript.text = "Good morning team."
        mock_transcript.utterances = [mock_utterance]
        mock_transcript.language_code = "en"
        mock_transcript.audio_duration = 2.0

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = mock_transcript
        mock_aai.Transcriber.return_value = mock_transcriber

        raw = assemblyai_bot._transcribe_assemblyai(DUMMY_AUDIO)

        assert raw["_provider"] == "assemblyai"
        assert raw["text"] == "Good morning team."
        assert len(raw["utterances"]) == 1

    @patch("modules.transcription.aai")
    def test_assemblyai_error_status_raises_provider_error(
        self, mock_aai: MagicMock, assemblyai_bot: Transcription
    ) -> None:
        """An 'error' transcript status raises STTProviderError."""
        mock_transcript = MagicMock()
        # Make status compare equal to TranscriptStatus.error
        mock_transcript.status = mock_aai.TranscriptStatus.error
        mock_transcript.error = "Audio format unsupported"

        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = mock_transcript
        mock_aai.Transcriber.return_value = mock_transcriber

        with pytest.raises(STTProviderError, match="Audio format unsupported"):
            assemblyai_bot._transcribe_assemblyai(DUMMY_AUDIO)


# ---------------------------------------------------------------------------
# T009 – _normalise for all three provider payloads
# ---------------------------------------------------------------------------

class TestNormalise:
    """T009 – _normalise maps all three providers to identical TranscriptResult shape."""

    REQUIRED_KEYS = {
        "full_text",
        "segments",
        "language",
        "duration_seconds",
        "provider",
        "diarisation_available",
    }
    SEGMENT_KEYS = {"speaker", "start_time", "end_time", "text"}

    def _assert_result_shape(self, result: dict) -> None:
        assert self.REQUIRED_KEYS == set(result.keys()), f"Missing keys: {self.REQUIRED_KEYS - set(result.keys())}"
        assert isinstance(result["full_text"], str)
        assert isinstance(result["segments"], list)
        assert isinstance(result["language"], str)
        assert isinstance(result["duration_seconds"], float)
        assert isinstance(result["provider"], str)
        assert isinstance(result["diarisation_available"], bool)
        for seg in result["segments"]:
            assert self.SEGMENT_KEYS.issubset(set(seg.keys()))
            assert isinstance(seg["start_time"], float)
            assert isinstance(seg["end_time"], float)
            assert isinstance(seg["text"], str)

    def test_normalise_whisper(self, whisper_bot: Transcription) -> None:
        result = whisper_bot._normalise(WHISPER_RAW)
        self._assert_result_shape(result)
        assert result["provider"] == "whisper"
        assert result["diarisation_available"] is False
        assert all(seg["speaker"] is None for seg in result["segments"])
        assert result["full_text"] == "Hello world. This is a test."
        assert result["duration_seconds"] == 5.0

    def test_normalise_deepgram(self, deepgram_bot: Transcription) -> None:
        result = deepgram_bot._normalise(DEEPGRAM_RAW)
        self._assert_result_shape(result)
        assert result["provider"] == "deepgram"
        assert result["diarisation_available"] is True
        # Should have produced 2 speaker segments (speaker 0 and speaker 1)
        assert len(result["segments"]) == 2
        assert result["segments"][0]["speaker"] == "Speaker 0"
        assert result["segments"][1]["speaker"] == "Speaker 1"

    def test_normalise_assemblyai(self, assemblyai_bot: Transcription) -> None:
        result = assemblyai_bot._normalise(ASSEMBLYAI_RAW)
        self._assert_result_shape(result)
        assert result["provider"] == "assemblyai"
        assert result["diarisation_available"] is True
        assert result["segments"][0]["speaker"] == "Speaker A"
        # milliseconds → seconds
        assert result["segments"][0]["start_time"] == 0.0
        assert result["segments"][0]["end_time"] == 2.0

    def test_normalise_raises_on_bad_deepgram_structure(self, deepgram_bot: Transcription) -> None:
        """Missing 'results' key triggers NormalisationError (TR-005)."""
        bad_raw = {"_provider": "deepgram", "metadata": {}}
        with pytest.raises(NormalisationError):
            deepgram_bot._normalise(bad_raw)


# ---------------------------------------------------------------------------
# T014 – HTTP 408 retry loop exhausts → STTTimeoutError
# ---------------------------------------------------------------------------

class TestRetryOnTimeout:
    """T014 – 408 responses trigger exponential backoff; exhaustion raises STTTimeoutError."""

    @patch("modules.transcription.time.sleep")
    @patch("os.path.getsize", return_value=1024)
    def test_408_retries_three_times_then_raises(
        self, mock_size: MagicMock, mock_sleep: MagicMock, whisper_bot: Transcription
    ) -> None:
        """After _RETRY_ATTEMPTS consecutive timeouts, STTTimeoutError is raised."""
        with patch.object(whisper_bot, "_dispatch", side_effect=STTTimeoutError("whisper", 1)):
            with pytest.raises(STTTimeoutError) as exc_info:
                whisper_bot.transcribe(DUMMY_AUDIO)

        assert "whisper" in str(exc_info.value)
        # sleep should be called between retries (not on last attempt)
        assert mock_sleep.call_count == 2

    @patch("modules.transcription.time.sleep")
    @patch("os.path.getsize", return_value=1024)
    def test_408_backoff_values_are_bounded(
        self, mock_size: MagicMock, mock_sleep: MagicMock, whisper_bot: Transcription
    ) -> None:
        """Sleep values follow min(2^attempt * 5, 20) pattern."""
        with patch.object(whisper_bot, "_dispatch", side_effect=STTTimeoutError("whisper", 1)):
            with pytest.raises(STTTimeoutError):
                whisper_bot.transcribe(DUMMY_AUDIO)

        sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
        # attempt 0 → sleep(5), attempt 1 → sleep(10)
        assert sleep_calls[0] == 5
        assert sleep_calls[1] == 10


# ---------------------------------------------------------------------------
# T015 – HTTP 429 triggers provider fallback switch
# ---------------------------------------------------------------------------

class TestFallbackOnRateLimit:
    """T015 – 429 causes the router to switch to the next provider."""

    @patch("os.path.getsize", return_value=1024)
    def test_429_switches_provider_and_retries(
        self, mock_size: MagicMock, whisper_bot: Transcription
    ) -> None:
        """STTRateLimitError causes provider switch; second successful call returns result."""
        mock_result: TranscriptResult = {
            "full_text": "ok",
            "segments": [],
            "language": "en",
            "duration_seconds": 1.0,
            "provider": "deepgram",
            "diarisation_available": True,
        }

        call_count = {"n": 0}

        def side_effect(path: str) -> dict:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise STTRateLimitError("whisper")
            return DEEPGRAM_RAW  # raw dict — will be normalised

        with patch.object(whisper_bot, "_dispatch", side_effect=side_effect):
            with patch.object(whisper_bot, "_normalise", return_value=mock_result):
                result = whisper_bot.transcribe(DUMMY_AUDIO)

        assert result["provider"] == "deepgram"
        # Provider state should have been mutated to the fallback
        assert whisper_bot.provider == "deepgram"

    @patch("os.path.getsize", return_value=1024)
    def test_429_fallback_order_whisper_to_deepgram(
        self, mock_size: MagicMock, whisper_bot: Transcription
    ) -> None:
        """Whisper → Deepgram is the defined fallback order."""
        from modules.transcription import _FALLBACK_ORDER
        assert _FALLBACK_ORDER["whisper"] == "deepgram"
        assert _FALLBACK_ORDER["deepgram"] == "assemblyai"


# ---------------------------------------------------------------------------
# T016 – HTTP 401 causes instant dropout without backoff
# ---------------------------------------------------------------------------

class TestAuthError:
    """T016 – 401 Unauthorized should raise STTProviderError instantly (no sleep)."""

    @patch("modules.transcription.time.sleep")
    @patch("os.path.getsize", return_value=1024)
    def test_401_raises_provider_error_immediately(
        self, mock_size: MagicMock, mock_sleep: MagicMock, whisper_bot: Transcription
    ) -> None:
        """An STTProviderError (not timeout/rate-limit) must propagate without sleeping."""
        with patch.object(
            whisper_bot,
            "_dispatch",
            side_effect=STTProviderError("whisper", "401 Unauthorized"),
        ):
            with pytest.raises(STTProviderError, match="401 Unauthorized"):
                whisper_bot.transcribe(DUMMY_AUDIO)

        # No sleep calls should have been made
        mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# T019 – File > 25 MB triggers AudioTooLargeError before any API call
# ---------------------------------------------------------------------------

class TestFileSizeGuard:
    """T019 – Files larger than 25 MB must raise AudioTooLargeError immediately."""

    @patch("os.path.getsize", return_value=_25MB_PLUS_1)
    def test_large_file_raises_audio_too_large(
        self, mock_size: MagicMock, whisper_bot: Transcription
    ) -> None:
        """26 MB file raises AudioTooLargeError before _dispatch is ever called."""
        with patch.object(whisper_bot, "_dispatch") as mock_dispatch:
            with pytest.raises(AudioTooLargeError) as exc_info:
                whisper_bot.transcribe(DUMMY_AUDIO)

        mock_dispatch.assert_not_called()
        assert exc_info.value.size_bytes == _25MB_PLUS_1

    @patch("os.path.getsize", return_value=25 * 1024 * 1024)
    def test_exact_25mb_is_allowed(
        self, mock_size: MagicMock, whisper_bot: Transcription
    ) -> None:
        """A file exactly at the limit should NOT raise AudioTooLargeError."""
        with patch.object(whisper_bot, "_dispatch", return_value=WHISPER_RAW):
            with patch.object(whisper_bot, "_normalise", return_value={
                "full_text": "ok",
                "segments": [],
                "language": "en",
                "duration_seconds": 0.0,
                "provider": "whisper",
                "diarisation_available": False,
            }):
                result = whisper_bot.transcribe(DUMMY_AUDIO)

        assert result is not None

    @patch("os.path.getsize", return_value=500 * 1024 * 1024 + 1)
    def test_large_file_error_contains_path(
        self, mock_size: MagicMock, deepgram_bot: Transcription
    ) -> None:
        """AudioTooLargeError stores the file path for debugging (Deepgram > 500MB)."""
        with pytest.raises(AudioTooLargeError) as exc_info:
            deepgram_bot.transcribe(DUMMY_AUDIO)

        assert exc_info.value.path == DUMMY_AUDIO


# ---------------------------------------------------------------------------
# T022 – Type-hint / schema contract tests
# ---------------------------------------------------------------------------

class TestSchemaContract:
    """T022 – Normalised output must conform strictly to the data-model.md schema."""

    def test_whisper_all_segments_have_none_speaker(self, whisper_bot: Transcription) -> None:
        result = whisper_bot._normalise(WHISPER_RAW)
        for seg in result["segments"]:
            assert seg["speaker"] is None

    def test_deepgram_segment_times_are_floats(self, deepgram_bot: Transcription) -> None:
        result = deepgram_bot._normalise(DEEPGRAM_RAW)
        for seg in result["segments"]:
            assert isinstance(seg["start_time"], float)
            assert isinstance(seg["end_time"], float)

    def test_assemblyai_milliseconds_converted_to_seconds(self, assemblyai_bot: Transcription) -> None:
        result = assemblyai_bot._normalise(ASSEMBLYAI_RAW)
        # utterance end=2000ms should become 2.0s
        assert result["segments"][0]["end_time"] == 2.0
