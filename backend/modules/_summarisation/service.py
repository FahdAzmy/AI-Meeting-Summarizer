"""Summarisation service facade implementation."""

from __future__ import annotations

import logging
from typing import Any

import openai

from config.settings import Config
from modules.llm_errors import EmptyTranscriptError, LLMAPIError, LLMTimeoutError
from modules._summarisation.analytics import analyse_participation
from modules._summarisation.parsing import parse_meeting_report
from modules._summarisation.prompts import SUMMARY_SYSTEM_PROMPT
from modules._summarisation.schemas import MeetingReportSchema
from modules._summarisation.speaker_detection import detect_speakers_from_text

logger = logging.getLogger(__name__)


class Summarisation:
    """Provider-agnostic LLM orchestrator for meeting summaries and analytics."""

    _TEMPERATURE: float = 0.3

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        config: Config | None = None,
    ):
        self._config = config or Config()
        self.model: str = model or self._config.LLM_MODEL
        self.temperature: float = (
            temperature if temperature is not None else self._TEMPERATURE
        )
        self._timeout: int = self._config.LLM_TIMEOUT

        openai_module = self._openai_module()
        self._client = openai_module.OpenAI(
            api_key=self._config.LLM_API_KEY or "no-key",
            base_url=self._config.LLM_BASE_URL,
        )

        logger.info(
            "[SM] Summarisation initialised. provider=%s model=%s timeout=%ds",
            self._config.LLM_BASE_URL,
            self.model,
            self._timeout,
        )

    def _openai_module(self):
        return openai

    def close(self) -> None:
        """Close the underlying LLM client when supported by the SDK."""
        close_method = getattr(self._client, "close", None)
        if callable(close_method):
            close_method()

    def __enter__(self) -> "Summarisation":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _call_llm(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        purpose: str,
    ) -> str:
        """Call the configured LLM, preferring JSON Mode with plain fallback."""
        try:
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=self._timeout,
                )
            except self._openai_module().BadRequestError:
                logger.warning(
                    "[SM] %s: JSON Mode unsupported - retrying without response_format.",
                    purpose,
                )
                response = self._client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=self._timeout,
                )
        except self._openai_module().APITimeoutError as exc:
            logger.error("[SM] LLM request timed out: %s", exc)
            raise LLMTimeoutError(timeout_seconds=self._timeout, cause=exc) from exc
        except self._openai_module().APIError as exc:
            logger.error("[SM] LLM API error: %s", exc)
            raise LLMAPIError(cause=exc) from exc

        return response.choices[0].message.content or ""

    def _generate_summary(self, transcript: dict[str, Any]) -> MeetingReportSchema:
        """Send transcript text to the LLM and parse the structured response."""
        full_text = transcript["full_text"]
        user_prompt = f"Meeting transcript:\n\n{full_text}"

        logger.info(
            "[SM] Sending transcript to LLM. provider=%s model=%s temperature=%s chars=%d",
            self._config.LLM_BASE_URL,
            self.model,
            self.temperature,
            len(full_text),
        )

        raw_content = self._call_llm(
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=self.temperature,
            purpose="Summary generation",
        )
        logger.info("[SM] LLM response received. length=%d chars", len(raw_content))

        try:
            return parse_meeting_report(raw_content)
        except Exception:
            logger.error("[SM] Failed to parse LLM response.")
            raise

    def _detect_speakers_from_text(
        self,
        transcript: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Use the LLM to split transcript text into per-speaker turns."""
        return detect_speakers_from_text(transcript, call_llm=self._call_llm)

    def generate_report(self, transcript: dict[str, Any]) -> dict[str, Any]:
        """Summarise the transcript and compute participation analytics."""
        if not transcript.get("full_text", "").strip():
            logger.warning("[SM] Transcript is empty \u2013 aborting summarisation.")
            raise EmptyTranscriptError()

        logger.info("[SM] Starting summarisation pipeline.")
        structured = self._generate_summary(transcript)

        segments = transcript.get("segments", [])
        speaker_stats: dict | None = None
        text_speaker_analysis: dict | None = None

        if transcript.get("diarisation_available") and segments:
            logger.info("[SM] Computing speaker analytics from STT diarisation data.")
            speaker_stats = analyse_participation(
                segments,
                detection_method="stt_diarisation",
            )

        if segments:
            logger.info(
                "[SM] Running LLM-based text speaker analysis (context detection)."
            )
            enriched_segments = self._detect_speakers_from_text(transcript)
            text_speaker_analysis = analyse_participation(
                enriched_segments,
                detection_method="llm_inferred",
            )
            if text_speaker_analysis:
                logger.info(
                    "[SM] LLM text speaker analysis complete: %d speakers found.",
                    len(text_speaker_analysis.get("speakers", [])),
                )

        report: dict[str, Any] = {
            "summary": structured.summary,
            "action_items": [item.model_dump() for item in structured.action_items],
            "decisions": structured.decisions,
            "follow_up": structured.follow_up,
            "speaker_stats": speaker_stats,
            "text_speaker_analysis": text_speaker_analysis,
        }

        logger.info("[SM] Report generation complete.")
        return report
