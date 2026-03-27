"""
modules/audio_capture.py
------------------------
Audio Capture Module – OBS WebSocket integration.

Manages system audio recording during virtual meetings by communicating with a
running OBS Studio instance over its WebSocket API (obsws-python).

Classes
-------
    AudioCapture
        High-level lifecycle controller: connect → health-check → start → stop.

Exceptions raised (defined in modules/errors.py)
-------------------------------------------------
    OBSConnectionError  (AC-001) – Bad credentials / unreachable host.
    OBSNotRunning       (AC-002) – OBS not running / WebSocket disabled.
    RecordingStartError (AC-003) – OBS refused start_record().
    RecordingStopError  (AC-004) – OBS refused stop_record().
    EmptyRecordingError (AC-005) – Output file is 0 bytes.
"""

import logging
import os

import obsws_python as obs

from config.settings import Config
from modules.errors import (
    EmptyRecordingError,
    OBSConnectionError,
    OBSNotRunning,
    RecordingStartError,
    RecordingStopError,
)

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    OBS WebSocket bridge for programmatic audio recording control.

    Parameters
    ----------
    config : Config | None
        An optional pre-built ``Config`` instance.  When *None* a fresh
        instance is constructed (reads from environment / .env).

    Attributes
    ----------
    host : str
    port : int
    password : str
    client : obs.ReqClient | None
        Active WebSocket connection, set during ``__init__``.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, config: Config | None = None) -> None:
        cfg: Config = config or Config()

        self.host: str = cfg.OBS_HOST
        self.port: int = cfg.OBS_PORT
        self.password: str = cfg.OBS_PASSWORD
        self._recordings_dir: str = cfg.RECORDINGS_DIR

        logger.debug(
            "AudioCapture initialising – OBS target: %s:%s", self.host, self.port
        )

        # Ensure the recordings output directory exists.
        os.makedirs(self._recordings_dir, exist_ok=True)
        logger.debug("Recordings directory confirmed: %s", self._recordings_dir)

        try:
            self.client: obs.ReqClient = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password,
            )
            logger.info(
                "OBS WebSocket connection established at %s:%s", self.host, self.port
            )
        except Exception as exc:
            logger.error(
                "Failed to connect to OBS at %s:%s – %r", self.host, self.port, exc
            )
            raise OBSConnectionError(host=self.host, port=self.port, cause=exc) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def healthcheck(self) -> bool:
        """
        Verify that OBS is alive and the WebSocket server is reachable.

        Returns
        -------
        bool
            ``True`` when OBS responds correctly to a version ping.

        Raises
        ------
        OBSNotRunning
            When the client call fails, indicating OBS is unreachable.
        """
        logger.debug("Performing OBS healthcheck…")
        try:
            version_info = self.client.get_version()
            logger.info(
                "OBS healthcheck passed – OBS version: %s", version_info
            )
            return True
        except Exception as exc:
            logger.error("OBS healthcheck failed – %r", exc)
            raise OBSNotRunning(host=self.host, port=self.port) from exc

    def start(self) -> None:
        """
        Start an audio recording session via OBS.

        Steps
        -----
        1. Confirm OBS is healthy (``healthcheck()``).
        2. Call ``client.start_record()``.

        Raises
        ------
        OBSNotRunning
            Propagated from ``healthcheck()`` when OBS is unreachable.
        RecordingStartError
            When ``start_record()`` itself raises an exception.
        """
        logger.info("Requesting OBS to start recording…")

        # Gate: ensure OBS is alive before attempting to record.
        self.healthcheck()

        try:
            self.client.start_record()
            logger.info("OBS recording started successfully.")
        except Exception as exc:
            logger.error("OBS start_record() failed – %r", exc)
            raise RecordingStartError(cause=exc) from exc

    def stop(self) -> str:
        """
        Stop the active recording session and return the local file path.

        Steps
        -----
        1. Call ``client.stop_record()`` – OBS returns an output path.
        2. Validate that the returned file is non-empty.

        Returns
        -------
        str
            Absolute path to the saved ``.wav`` (or OBS-configured format) file.

        Raises
        ------
        RecordingStopError
            When ``stop_record()`` raises an exception.
        EmptyRecordingError
            When the resulting file is 0 bytes or the path cannot be resolved.
        """
        logger.info("Requesting OBS to stop recording…")

        try:
            response = self.client.stop_record()
            # obsws-python returns a StopRecordDataclass; try both naming
            # conventions (snake_case used by the library, camelCase from
            # the raw OBS protocol) before falling back to __dict__ inspection.
            output_path: str = (
                getattr(response, "output_path", None)
                or getattr(response, "outputPath", None)
                or (vars(response).get("output_path") if hasattr(response, "__dict__") else None)
                or (vars(response).get("outputPath") if hasattr(response, "__dict__") else None)
            )
            logger.debug(
                "OBS stop_record() response type: %s, attrs: %s",
                type(response).__name__,
                vars(response) if hasattr(response, "__dict__") else str(response),
            )
            logger.debug("OBS stop_record() returned path: %s", output_path)
        except Exception as exc:
            logger.error("OBS stop_record() failed – %r", exc)
            raise RecordingStopError(cause=exc) from exc

        # Validate the file is non-empty.
        if not output_path or not os.path.exists(output_path):
            logger.error("Recording file not found at path: %s", output_path)
            raise EmptyRecordingError(path=output_path or "<none>")

        file_size = os.path.getsize(output_path)
        if file_size == 0:
            logger.error("Recording file is 0 bytes: %s", output_path)
            raise EmptyRecordingError(path=output_path)

        logger.info(
            "Recording saved successfully – path: %s  size: %d bytes",
            output_path,
            file_size,
        )
        return output_path
