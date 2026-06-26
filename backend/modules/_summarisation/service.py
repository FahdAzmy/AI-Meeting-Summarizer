"""Summarisation service facade implementation."""

from __future__ import annotations

import json
import logging
from typing import Any

import openai

from config.settings import Config
from modules.llm_errors import EmptyTranscriptError, LLMAPIError, LLMTimeoutError
from modules._summarisation.analytics import analyse_participation, merge_speaker_names
from modules._summarisation.parsing import parse_meeting_report
from modules._summarisation.prompts import (
    SPEAKER_VERIFICATION_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
)
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
        *,
        participant_hints: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Use the LLM to split transcript text into per-speaker turns."""
        return detect_speakers_from_text(
            transcript,
            call_llm=self._call_llm,
            participant_hints=participant_hints,
        )

    def _verify_speaker_mapping(
        self,
        speaker_stats: dict[str, Any],
        transcript: dict[str, Any],
        participant_hints: list[str] | None = None,
    ) -> dict[str, Any]:
        """Use the LLM to verify and optionally correct the name mapping.

        This is Solution 4: after merging STT timing with LLM-inferred names,
        send both the transcript and the proposed mapping to the LLM for a
        second-opinion verification pass.
        """
        name_map = speaker_stats.get("name_mapping")
        if not name_map:
            return speaker_stats

        full_text = transcript.get("full_text", "")
        mapping_str = ", ".join(f"{k} → {v}" for k, v in name_map.items())

        hints_section = ""
        if participant_hints:
            hints_section = (
                f"\nKnown meeting participants: {', '.join(participant_hints)}"
            )

        user_prompt = (
            f"Meeting transcript:\n\n{full_text}\n\n"
            f"Proposed speaker mapping: {mapping_str}"
            f"{hints_section}\n\n"
            f"Verify whether this speaker-to-name mapping is correct."
        )

        try:
            raw = self._call_llm(
                system_prompt=SPEAKER_VERIFICATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.1,
                purpose="Speaker mapping verification",
            )
            result = json.loads(raw)
            verified_map = result.get("verified_mapping", {})
            confidence = result.get("confidence", "low")
            corrections = result.get("corrections_made", False)

            logger.info(
                "[SM] Speaker verification: confidence=%s corrections=%s",
                confidence,
                corrections,
            )

            # If low confidence or empty, keep the merge result as-is
            if not verified_map or confidence == "low":
                speaker_stats["verification_confidence"] = confidence
                return speaker_stats

            # Apply corrections if the LLM found errors
            if corrections:
                # Build reverse lookup: current_name → original_label
                reverse = {v: k for k, v in name_map.items()}

                updated_speakers = []
                for spk in speaker_stats.get("speakers", []):
                    new_spk = dict(spk)
                    current_name = spk["speaker"]
                    # Find the original generic label for this speaker
                    orig_label = reverse.get(current_name, current_name)
                    # Apply verified name (if available)
                    if orig_label in verified_map:
                        new_spk["speaker"] = verified_map[orig_label]
                    updated_speakers.append(new_spk)

                speaker_stats = dict(speaker_stats)
                speaker_stats["speakers"] = updated_speakers
                if updated_speakers:
                    speaker_stats["most_active_speaker"] = updated_speakers[0][
                        "speaker"
                    ]
                speaker_stats["name_mapping"] = verified_map

            speaker_stats["detection_method"] = (
                "stt_diarisation+llm_name_merge+llm_verified"
            )
            speaker_stats["verification_confidence"] = confidence
            return speaker_stats

        except Exception as exc:
            logger.warning(
                "[SM] Speaker verification failed (non-fatal): %s",
                exc,
            )
            return speaker_stats

    def generate_report(
        self,
        transcript: dict[str, Any],
        *,
        participant_hints: list[str] | None = None,
    ) -> dict[str, Any]:
        """Summarise the transcript and compute participation analytics.

        Parameters
        ----------
        participant_hints:
            Optional list of known participant names (e.g. extracted from
            email addresses).  Fed into the LLM speaker detection prompt
            (Solution 3) and the verification step (Solution 4).
        """
        if not transcript.get("full_text", "").strip():
            logger.warning("[SM] Transcript is empty – aborting summarisation.")
            raise EmptyTranscriptError()

        logger.info("[SM] Starting summarisation pipeline.")
        structured = self._generate_summary(transcript)

        segments = transcript.get("segments", [])
        speaker_stats: dict | None = None
        text_speaker_analysis: dict | None = None

        # ── Layer 1: STT diarisation analytics (accurate timing) ─────────
        if transcript.get("diarisation_available") and segments:
            logger.info("[SM] Computing speaker analytics from STT diarisation data.")
            speaker_stats = analyse_participation(
                segments,
                detection_method="stt_diarisation",
            )

        # ── Layer 2: LLM text speaker detection (real names) ─────────────
        if segments:
            logger.info(
                "[SM] Running LLM-based text speaker analysis (context detection)."
            )
            enriched_segments = self._detect_speakers_from_text(
                transcript,
                participant_hints=participant_hints,
            )
            text_speaker_analysis = analyse_participation(
                enriched_segments,
                detection_method="llm_inferred",
            )
            if text_speaker_analysis:
                logger.info(
                    "[SM] LLM text speaker analysis complete: %d speakers found.",
                    len(text_speaker_analysis.get("speakers", [])),
                )

        # ── Solution 1: Merge Layer 1 + Layer 2 (rank-based name mapping) ─
        if speaker_stats and text_speaker_analysis:
            stt_count = len(speaker_stats.get("speakers", []))
            llm_count = len(text_speaker_analysis.get("speakers", []))

            if stt_count == 1 and llm_count > 1:
                logger.warning(
                    "[SM] STT found only 1 speaker but LLM found %d. "
                    "STT diarisation failed. Falling back to LLM analysis.",
                    llm_count,
                )
                speaker_stats = text_speaker_analysis
            else:
                logger.info("[SM] Merging STT timing with LLM-inferred speaker names.")
                speaker_stats = merge_speaker_names(speaker_stats, text_speaker_analysis)

                # ── Solution 4: LLM verification of the merged mapping ────────
                if speaker_stats and speaker_stats.get("name_mapping"):
                    logger.info("[SM] Verifying speaker name mapping via LLM.")
                    speaker_stats = self._verify_speaker_mapping(
                        speaker_stats,
                        transcript,
                        participant_hints=participant_hints,
                    )
        elif text_speaker_analysis and not speaker_stats:
            logger.info("[SM] No STT diarisation data. Using LLM text analysis.")
            speaker_stats = text_speaker_analysis

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
