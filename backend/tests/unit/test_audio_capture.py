"""
tests/unit/test_audio_capture.py
---------------------------------
Comprehensive TDD unit-test suite for the AudioCapture module.

All obsws_python.ReqClient calls are mocked via unittest.mock so that:
  - No OBS Studio process needs to be running.
  - CI pipelines remain fast and deterministic.

Coverage
--------
  T005  Base fixture: ReqClient universally mocked.
  T006  __init__ uses Config credentials to instantiate ReqClient.
  T007  start() calls client.start_record() over the mocked socket.
  T008  stop() calls client.stop_record() and parses the path from output.
  T012  healthcheck() calls client.get_version() and returns True on success.
  T013  OBSConnectionError raised when ReqClient constructor raises.
  T014  start() raises OBSNotRunning if healthcheck() is forced to fail.
  T018  EmptyRecordingError raised when stop_record returns a 0-byte file path.
"""

import os
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Helpers – make sure imports resolve regardless of cwd
# ---------------------------------------------------------------------------
import sys

_BACKEND_ROOT = str(Path(__file__).resolve().parents[2])
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from config.settings import Config
from modules.audio_capture import AudioCapture
from modules.errors import (
    EmptyRecordingError,
    OBSConnectionError,
    OBSNotRunning,
    RecordingStartError,
    RecordingStopError,
)


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture()
def obs_config(tmp_path: Path) -> Config:
    """
    T005 – A Config object backed by real values so we can assert them,
    pointing RECORDINGS_DIR at pytest's tmp_path to avoid filesystem side
    effects.
    """
    return Config(
        OBS_HOST="testhost",
        OBS_PORT=4455,
        OBS_PASSWORD="supersecret",
        RECORDINGS_DIR=str(tmp_path / "recordings"),
    )


@pytest.fixture()
def mock_req_client() -> Generator[MagicMock, None, None]:
    """
    T005 – Universally mock obsws_python.ReqClient so that no real WebSocket
    connection is attempted during any test in this module.
    """
    with patch("modules.audio_capture.obs.ReqClient") as MockClient:
        instance = MagicMock()
        MockClient.return_value = instance
        yield MockClient


@pytest.fixture()
def capture(obs_config: Config, mock_req_client: MagicMock) -> AudioCapture:
    """
    Convenience fixture: an AudioCapture instance with a fully mocked OBS
    socket and a predictable Config.
    """
    return AudioCapture(config=obs_config)


# ===========================================================================
# T006 – __init__ uses Config credentials
# ===========================================================================

class TestInit:
    def test_req_client_called_with_config_values(
        self, obs_config: Config, mock_req_client: MagicMock
    ) -> None:
        """T006 – ReqClient must be instantiated using the host/port/password
        values pulled from the injected Config object."""
        AudioCapture(config=obs_config)

        mock_req_client.assert_called_once_with(
            host="testhost",
            port=4455,
            password="supersecret",
        )

    def test_recordings_dir_created(
        self, obs_config: Config, mock_req_client: MagicMock, tmp_path: Path
    ) -> None:
        """T006 – RECORDINGS_DIR is created on disk during __init__."""
        recordings_dir = tmp_path / "recordings"
        assert not recordings_dir.exists()

        AudioCapture(config=obs_config)

        assert recordings_dir.exists()

    def test_host_port_password_stored(
        self, capture: AudioCapture, obs_config: Config
    ) -> None:
        """T006 – Instance attributes must mirror the Config values."""
        assert capture.host == obs_config.OBS_HOST
        assert capture.port == obs_config.OBS_PORT
        assert capture.password == obs_config.OBS_PASSWORD


# ===========================================================================
# T013 – OBSConnectionError on ReqClient failure
# ===========================================================================

class TestInitConnectionError:
    def test_obs_connection_error_raised_when_client_raises(
        self, obs_config: Config
    ) -> None:
        """T013 – When the ReqClient constructor raises any exception the
        module must convert it to OBSConnectionError (AC-001)."""
        root_cause = ConnectionRefusedError("port closed")

        with patch(
            "modules.audio_capture.obs.ReqClient", side_effect=root_cause
        ):
            with pytest.raises(OBSConnectionError) as exc_info:
                AudioCapture(config=obs_config)

        err = exc_info.value
        assert err.code == "AC-001"
        assert err.host == obs_config.OBS_HOST
        assert err.port == obs_config.OBS_PORT
        assert err.cause is root_cause

    def test_obs_connection_error_message_format(
        self, obs_config: Config
    ) -> None:
        """T013 – Error message must include host and port."""
        with patch(
            "modules.audio_capture.obs.ReqClient",
            side_effect=Exception("boom"),
        ):
            with pytest.raises(OBSConnectionError) as exc_info:
                AudioCapture(config=obs_config)

        assert "testhost" in str(exc_info.value)
        assert "4455" in str(exc_info.value)


# ===========================================================================
# T012 – healthcheck()
# ===========================================================================

class TestHealthcheck:
    def test_healthcheck_calls_get_version(self, capture: AudioCapture) -> None:
        """T012 – healthcheck() must call client.get_version() exactly once."""
        capture.client.get_version.return_value = MagicMock(obsVersion="30.0.0")

        result = capture.healthcheck()

        capture.client.get_version.assert_called_once()
        assert result is True

    def test_healthcheck_returns_true_on_success(
        self, capture: AudioCapture
    ) -> None:
        """T012 – healthcheck() returns True when get_version() succeeds."""
        capture.client.get_version.return_value = MagicMock()
        assert capture.healthcheck() is True

    def test_healthcheck_raises_obs_not_running_on_failure(
        self, capture: AudioCapture
    ) -> None:
        """T013 – OBSNotRunning (AC-002) raised when get_version() raises."""
        capture.client.get_version.side_effect = ConnectionRefusedError("down")

        with pytest.raises(OBSNotRunning) as exc_info:
            capture.healthcheck()

        err = exc_info.value
        assert err.code == "AC-002"
        assert err.host == capture.host
        assert err.port == capture.port


# ===========================================================================
# T007 – start()
# ===========================================================================

class TestStart:
    def test_start_calls_start_record(self, capture: AudioCapture) -> None:
        """T007 – start() must call client.start_record() over the mocked
        socket after passing healthcheck."""
        capture.client.get_version.return_value = MagicMock()
        capture.client.start_record.return_value = None

        capture.start()

        capture.client.start_record.assert_called_once()

    def test_start_performs_healthcheck_first(
        self, capture: AudioCapture
    ) -> None:
        """T007 – start() must call get_version() before start_record()."""
        call_order: list[str] = []
        capture.client.get_version.side_effect = lambda: call_order.append("healthcheck") or MagicMock()
        capture.client.start_record.side_effect = lambda: call_order.append("start_record")

        capture.start()

        assert call_order == ["healthcheck", "start_record"]

    def test_start_raises_recording_start_error_on_obs_failure(
        self, capture: AudioCapture
    ) -> None:
        """T007 – start_record() raising must surface as RecordingStartError (AC-003)."""
        capture.client.get_version.return_value = MagicMock()
        root_cause = RuntimeError("OBS codec error")
        capture.client.start_record.side_effect = root_cause

        with pytest.raises(RecordingStartError) as exc_info:
            capture.start()

        err = exc_info.value
        assert err.code == "AC-003"
        assert err.cause is root_cause


# ===========================================================================
# T014 – start() fails when healthcheck() returns False / raises
# ===========================================================================

class TestStartHealthcheckGate:
    def test_start_raises_obs_not_running_when_healthcheck_fails(
        self, capture: AudioCapture
    ) -> None:
        """T014 – If healthcheck() raises OBSNotRunning, start() must NOT call
        start_record() and must propagate the OBSNotRunning exception."""
        capture.client.get_version.side_effect = Exception("OBS down")

        with pytest.raises(OBSNotRunning):
            capture.start()

        capture.client.start_record.assert_not_called()


# ===========================================================================
# T008 – stop()
# ===========================================================================

class TestStop:
    def _make_fake_recording(self, tmp_path: Path, size: int = 1024) -> str:
        """Write a fake WAV file and return its absolute path."""
        p = tmp_path / "meeting.wav"
        p.write_bytes(b"\x00" * size)
        return str(p)

    def test_stop_calls_stop_record(
        self, capture: AudioCapture, tmp_path: Path
    ) -> None:
        """T008 – stop() must call client.stop_record() exactly once."""
        fake_path = self._make_fake_recording(tmp_path)
        response = MagicMock()
        response.outputPath = fake_path
        response.output_path = fake_path
        capture.client.stop_record.return_value = response

        capture.stop()

        capture.client.stop_record.assert_called_once()

    def test_stop_returns_output_path(
        self, capture: AudioCapture, tmp_path: Path
    ) -> None:
        """T008 – stop() returns the path string parsed from the OBS response."""
        fake_path = self._make_fake_recording(tmp_path)
        response = MagicMock()
        response.outputPath = fake_path
        response.output_path = fake_path
        capture.client.stop_record.return_value = response

        result = capture.stop()

        assert result == fake_path

    def test_stop_raises_recording_stop_error_on_obs_failure(
        self, capture: AudioCapture
    ) -> None:
        """T008 – RecordingStopError (AC-004) raised when stop_record() raises."""
        root_cause = RuntimeError("OBS crash")
        capture.client.stop_record.side_effect = root_cause

        with pytest.raises(RecordingStopError) as exc_info:
            capture.stop()

        err = exc_info.value
        assert err.code == "AC-004"
        assert err.cause is root_cause


# ===========================================================================
# T018 – EmptyRecordingError when file is 0 bytes
# ===========================================================================

class TestEmptyRecording:
    def test_empty_file_raises_empty_recording_error(
        self, capture: AudioCapture, tmp_path: Path
    ) -> None:
        """T018 – When OBS returns a path to a 0-byte file, stop() must raise
        EmptyRecordingError (AC-005) to prevent silent data losses downstream."""
        empty_file = tmp_path / "empty.wav"
        empty_file.write_bytes(b"")  # 0 bytes

        response = MagicMock()
        response.outputPath = str(empty_file)
        response.output_path = str(empty_file)
        capture.client.stop_record.return_value = response

        with pytest.raises(EmptyRecordingError) as exc_info:
            capture.stop()

        err = exc_info.value
        assert err.code == "AC-005"
        # err.path holds the raw path; str(err) contains repr() of it (escaped
        # backslashes on Windows), so compare via the attribute instead.
        assert err.path == str(empty_file)

    def test_missing_path_raises_empty_recording_error(
        self, capture: AudioCapture
    ) -> None:
        """T018 – When the returned path does not exist on disk, EmptyRecordingError
        must be raised (file-not-found counts as unresolvable)."""
        response = MagicMock()
        response.outputPath = "/nonexistent/path/recording.wav"
        response.output_path = "/nonexistent/path/recording.wav"
        capture.client.stop_record.return_value = response

        with pytest.raises(EmptyRecordingError):
            capture.stop()

    def test_none_output_path_raises_empty_recording_error(
        self, capture: AudioCapture
    ) -> None:
        """T018 – Edge-case: OBS response carries no path attribute at all."""
        response = MagicMock(spec=[])  # no attributes → getattr returns None
        capture.client.stop_record.return_value = response

        with pytest.raises(EmptyRecordingError):
            capture.stop()


# ===========================================================================
# T021 – Full pytest run guard (smoke test)
# ===========================================================================

class TestSmokeFullSuite:
    def test_all_exception_codes_correct(self) -> None:
        """T021 – Verify every custom AC exception carries the right error code."""
        from modules.errors import (
            OBSConnectionError,
            OBSNotRunning,
            RecordingStartError,
            RecordingStopError,
            EmptyRecordingError,
        )
        assert OBSConnectionError("h", 1).code == "AC-001"
        assert OBSNotRunning().code == "AC-002"
        assert RecordingStartError().code == "AC-003"
        assert RecordingStopError().code == "AC-004"
        assert EmptyRecordingError("/tmp/x").code == "AC-005"

    def test_audio_capture_module_importable(self) -> None:
        """T021 – Ensure the module can be imported without side effects."""
        import importlib
        import modules.audio_capture as m
        importlib.reload(m)  # re-import to confirm no top-level side effects
        assert hasattr(m, "AudioCapture")
