"""
modules/summarisation.py
------------------------
Summarisation & Analysis Module – AI Meeting Summarizer pipeline.

Responsibilities
----------------
  1. Accept a standardised TranscriptResult dict from the Transcription module.
  2. Drive the full text through any OpenAI-compatible LLM using JSON Mode to
     extract a structured MeetingReport payload.
  3. Compute equitable speaker participation metrics when diarisation data is
     present in the transcript segments.
  4. Return a clean MeetingReport dict to the caller (API / orchestrator layer).

Provider-agnostic design
-------------------------
  The module uses the OpenAI Python SDK with a configurable ``base_url``, which
  means it works with ANY OpenAI-compatible provider out of the box:
    - OpenAI       : LLM_BASE_URL=https://api.openai.com/v1
    - OpenRouter   : LLM_BASE_URL=https://openrouter.ai/api/v1
    - Groq         : LLM_BASE_URL=https://api.groq.com/openai/v1
    - Mistral      : LLM_BASE_URL=https://api.mistral.ai/v1
    - Ollama       : LLM_BASE_URL=http://localhost:11434/v1
  Switch providers entirely through .env — zero code changes required.

Error Codes (defined in modules/llm_errors.py)
  SM-001  LLMAPIError          – HTTP-level failure from the LLM provider.
  SM-002  LLMTimeoutError      – Generation stalled beyond the timeout boundary.
  SM-003  ParseError           – JSON schema mismatch from the LLM response.
  SM-004  EmptyTranscriptError – Transcript contained no text; fast-exit guard.

Usage
-----
    from modules.summarisation import Summarisation

    bot = Summarisation()
    report = bot.generate_report(transcript_dict)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import openai
from pydantic import BaseModel, Field, ValidationError

from config.settings import Config
from modules.llm_errors import (
    EmptyTranscriptError,
    LLMAPIError,
    LLMTimeoutError,
    ParseError,
)

logger = logging.getLogger(__name__)

# Module-level config instance (reads from .env automatically)
_cfg = Config()

# ---------------------------------------------------------------------------
# Pydantic output schemas (strict JSON Mode binding)
# ---------------------------------------------------------------------------


class ActionItem(BaseModel):
    """A single accountable task extracted from the meeting."""

    assignee: str
    task: str
    deadline: str | None = None


class MeetingReportSchema(BaseModel):
    """Strict Pydantic schema for the LLM JSON output."""

    summary: str = Field(..., description="Markdown-formatted meeting overview.")
    action_items: list[ActionItem] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    follow_up: list[str] = Field(default_factory=list)


class SpeakerTurn(BaseModel):
    """A single conversation turn identified by the LLM from transcript text."""

    speaker: str = Field(..., description="Speaker name or label (e.g. 'Mr. Ahmed', 'Speaker 1').")
    text: str = Field(..., description="The exact text spoken in this turn.")


class SpeakerDetectionSchema(BaseModel):
    """Strict Pydantic schema for LLM-based text speaker detection output."""

    turns: list[SpeakerTurn] = Field(default_factory=list)
    speakers_identified: int = Field(0, description="Total unique speakers detected.")


# ---------------------------------------------------------------------------
# Speaker participation analytics helpers
# ---------------------------------------------------------------------------


def _analyse_participation(segments: list[dict[str, Any]]) -> dict | None:
    """
    Compute per-speaker speaking time from diarised segments.

    Parameters
    ----------
    segments : list of dicts
        Each segment is expected to have at least:
          - ``speaker``    (str)   e.g. "Speaker 0"
          - ``start_time`` (float) start time in seconds
          - ``end_time``   (float) end time in seconds

    Returns
    -------
    dict | None
        Participation stats, or None if segments has no diarisation data.
    """
    if not segments:
        return None

    # Filter to segments that actually carry a speaker label
    diarised = [s for s in segments if s.get("speaker")]
    if not diarised:
        return None

    speaker_time: dict[str, float] = {}
    speaker_turns: dict[str, int] = {}

    for seg in diarised:
        speaker = seg["speaker"]
        # Support both key conventions: start_time/end_time (normalised) and start/end (raw)
        start = float(seg.get("start_time", seg.get("start", 0)))
        end = float(seg.get("end_time", seg.get("end", 0)))
        duration = end - start
        speaker_time[speaker] = speaker_time.get(speaker, 0.0) + max(duration, 0.0)
        speaker_turns[speaker] = speaker_turns.get(speaker, 0) + 1

    total_duration = sum(speaker_time.values())
    if total_duration == 0:
        return None

    speakers_list = [
        {
            "speaker": spk,
            "total_speaking_time_sec": round(speaker_time[spk], 3),
            "percentage_of_meeting": round(
                (speaker_time[spk] / total_duration) * 100, 2
            ),
            "number_of_turns": speaker_turns[spk],
        }
        for spk in sorted(speaker_time, key=lambda s: speaker_time[s], reverse=True)
    ]

    most_active = speakers_list[0]["speaker"]

    return {
        "speakers": speakers_list,
        "most_active_speaker": most_active,
        "total_meeting_duration_sec": round(total_duration, 3),
    }


# ---------------------------------------------------------------------------
# Main orchestrator class
# ---------------------------------------------------------------------------


class Summarisation:
    """
    Provider-agnostic LLM orchestrator for meeting summarisation and analytics.

    Reads all provider settings from the environment / .env file:
      - LLM_API_KEY  : API key for your chosen provider.
      - LLM_BASE_URL : Provider endpoint (OpenAI, OpenRouter, Groq, Ollama …).
      - LLM_MODEL    : Model identifier (varies per provider).
      - LLM_TIMEOUT  : Maximum response wait time in seconds.

    Parameters
    ----------
    model : str, optional
        Override ``LLM_MODEL`` from env.
    temperature : float, optional
        Sampling temperature. Defaults to 0.3 (low = factual, no hallucinations).
    """

    _TEMPERATURE: float = 0.3

    def __init__(self, model: str | None = None, temperature: float | None = None):
        self.model: str = model or _cfg.LLM_MODEL
        self.temperature: float = temperature if temperature is not None else self._TEMPERATURE
        self._timeout: int = _cfg.LLM_TIMEOUT

        # Build a single reusable client pointed at the configured provider.
        self._client = openai.OpenAI(
            api_key=_cfg.LLM_API_KEY or "no-key",  # Ollama doesn't need a real key
            base_url=_cfg.LLM_BASE_URL,
        )

        logger.info(
            "[SM] Summarisation initialised. provider=%s model=%s timeout=%ds",
            _cfg.LLM_BASE_URL,
            self.model,
            self._timeout,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_summary(self, transcript: dict[str, Any]) -> MeetingReportSchema:
        """
        Send the transcript to the LLM and parse the structured JSON response.

        Parameters
        ----------
        transcript : dict
            The standardised TranscriptResult dict with at least ``full_text``.

        Returns
        -------
        MeetingReportSchema
            Parsed Pydantic model from the LLM JSON output.

        Raises
        ------
        LLMAPIError
            On HTTP-level failures from the OpenAI endpoint.
        LLMTimeoutError
            When the request stalls or times out.
        ParseError
            When the LLM response cannot be parsed into the expected schema.
        """
        full_text = transcript["full_text"]

        system_prompt = (
            "You are an expert meeting analyst. "
            "Extract a structured JSON object from the meeting transcript provided. "
            "Your response MUST be valid JSON matching this schema exactly:\n"
            "{\n"
            '  "summary": "<markdown-formatted overview>",\n'
            '  "action_items": [{"assignee": "<name>", "task": "<task>", "deadline": "<date or null>"}],\n'
            '  "decisions": ["<decision 1>", ...],\n'
            '  "follow_up": ["<follow-up point 1>", ...]\n'
            "}\n"
            "CRITICAL LANGUAGE RULE: First, identify the primary language written in the transcript text below. "
            "If the transcript text is written in Arabic, you MUST formulate your entire JSON response (summary, tasks, decisions, etc.) in Arabic. "
            "If the transcript text is written in English, you MUST formulate your entire JSON response in English. "
            "Do NOT invent information not present in the transcript. "
            "Be concise and factual. Return ONLY the JSON object."
        )

        user_prompt = f"Meeting transcript:\n\n{full_text}"

        logger.info(
            "[SM] Sending transcript to LLM. provider=%s model=%s temperature=%s chars=%d",
            _cfg.LLM_BASE_URL,
            self.model,
            self.temperature,
            len(full_text),
        )

        try:
            # Attempt with JSON Mode first (supported by OpenAI, OpenRouter, Groq, Mistral).
            # Some providers (e.g. older Ollama models) don't support response_format,
            # so we fall back to plain-text parsing on BadRequestError.
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=self._timeout,
                )
            except openai.BadRequestError:
                # Provider doesn't support JSON Mode – retry without it.
                logger.warning(
                    "[SM] Provider does not support JSON Mode – retrying without response_format."
                )
                response = self._client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=self._timeout,
                )
        except openai.APITimeoutError as exc:
            logger.error("[SM] LLM request timed out: %s", exc)
            raise LLMTimeoutError(timeout_seconds=self._timeout, cause=exc) from exc
        except openai.APIError as exc:
            logger.error("[SM] LLM API error: %s", exc)
            raise LLMAPIError(cause=exc) from exc

        raw_content = response.choices[0].message.content or ""
        logger.info("[SM] LLM response received. length=%d chars", len(raw_content))

        try:
            payload = json.loads(raw_content)
            return MeetingReportSchema(**payload)
        except (json.JSONDecodeError, ValidationError, TypeError, KeyError) as exc:
            logger.error("[SM] Failed to parse LLM response: %s", exc)
            raise ParseError(
                message=f"LLM returned unparseable output: {raw_content[:200]!r}",
                cause=exc,
            ) from exc

    # ------------------------------------------------------------------
    # LLM-based speaker detection fallback
    # ------------------------------------------------------------------

    def _detect_speakers_from_text(
        self, transcript: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Use the LLM to split transcript text into per-speaker conversation turns.

        Unlike STT diarisation which relies on audio signals, this method analyses
        the **text content** to identify speakers from contextual clues: names
        mentioned, greeting patterns, question-answer flow, and role references.

        This is critical when STT sees only 1 speaker (e.g. shared microphone)
        but the text clearly contains multiple participants.

        The method distributes the total meeting duration proportionally based
        on word count per speaker turn.

        Parameters
        ----------
        transcript : dict
            The standardised TranscriptResult dict.

        Returns
        -------
        list[dict]
            Synthetic segments with speaker labels and proportional timestamps.
            Falls back to the original segments unchanged if detection fails.
        """
        full_text = transcript.get("full_text", "")
        if not full_text.strip():
            return transcript.get("segments", [])

        total_duration = float(transcript.get("duration_seconds", 0.0))

        system_prompt = (
            "You are an expert meeting analyst specialising in speaker identification. "
            "Below is a meeting transcript. The speech-to-text system recorded everything "
            "as a single block of text without identifying individual speakers.\n\n"
            "Your task is to SPLIT this text into individual conversation turns and identify "
            "who is speaking in each turn using contextual clues:\n"
            "  - Names mentioned (e.g. 'Thanks Ahmed', 'Hi Mr. Fahd')\n"
            "  - Greeting and farewell patterns (first speaker usually greets)\n"
            "  - Question-answer pairs (different speakers)\n"
            "  - Role references ('As the manager...', 'I finished my task...')\n"
            "  - Instructions vs. status updates (manager gives orders, team reports)\n\n"
            "RULES:\n"
            "1. Split the text at natural speaker change points.\n"
            "2. ALWAYS use the participant's REAL NAME as the speaker label. "
            "Look for names in greetings (e.g. 'Hello Mr. Fahd'), addresses "
            "(e.g. 'Okay Mr. Ahmed'), and references throughout the text. "
            "Only use generic labels like 'Speaker 1' as a LAST RESORT when "
            "absolutely no name can be found anywhere in the transcript.\n"
            "3. Be consistent - same person must always get the same name label.\n"
            "4. Each turn's 'text' must be the EXACT words from the transcript (no rewording).\n"
            "5. The concatenation of all turns must reproduce the full transcript.\n"
            "6. Minimum 2 turns if you detect at least 2 different speakers.\n\n"
            "Your response MUST be valid JSON matching this schema exactly:\n"
            "{\n"
            '  "turns": [{"speaker": "<name>", "text": "<exact words from transcript>"}, ...],\n'
            '  "speakers_identified": <int>\n'
            "}\n"
            "Return ONLY the JSON object."
        )

        user_prompt = f"Full meeting transcript:\n\n{full_text}"

        logger.info(
            "[SM] Text speaker detection: sending full transcript to LLM (%d chars).",
            len(full_text),
        )

        try:
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    temperature=0.1,  # very low - factual inference
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=self._timeout,
                )
            except openai.BadRequestError:
                logger.warning(
                    "[SM] Text speaker detection: JSON Mode unsupported - retrying."
                )
                response = self._client.chat.completions.create(
                    model=self.model,
                    temperature=0.1,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=self._timeout,
                )

            raw_content = response.choices[0].message.content or ""
            payload = json.loads(raw_content)
            detection = SpeakerDetectionSchema(**payload)

            logger.info(
                "[SM] Text speaker detection complete: %d speakers, %d turns.",
                detection.speakers_identified,
                len(detection.turns),
            )

            if not detection.turns:
                return transcript.get("segments", [])

            # Distribute total_duration proportionally by word count per turn
            total_words = sum(len(t.text.split()) for t in detection.turns)
            if total_words == 0:
                total_words = 1  # safety

            enriched_segments: list[dict[str, Any]] = []
            current_time = 0.0

            for turn in detection.turns:
                word_count = len(turn.text.split())
                turn_duration = (word_count / total_words) * total_duration if total_duration > 0 else 1.0

                enriched_segments.append({
                    "speaker": turn.speaker,
                    "start_time": round(current_time, 3),
                    "end_time": round(current_time + turn_duration, 3),
                    "text": turn.text,
                })
                current_time += turn_duration

            return enriched_segments

        except Exception as exc:
            # Speaker detection is best-effort - never break the pipeline
            logger.warning(
                "[SM] Text speaker detection failed (non-fatal): %s", exc
            )
            return transcript.get("segments", [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_report(self, transcript: dict[str, Any]) -> dict[str, Any]:
        """
        Top-level orchestrator: summarise the transcript and compute analytics.

        Parameters
        ----------
        transcript : dict
            TranscriptResult dict with keys:
              - ``full_text``             (str)  Full meeting transcript text.
              - ``segments``              (list) Diarised segments (may be empty).
              - ``diarisation_available`` (bool) Whether diarisation was performed.
              - ``duration_seconds``      (float) Total meeting duration.

        Returns
        -------
        dict
            MeetingReport payload compatible with the frontend React parser.

        Raises
        ------
        EmptyTranscriptError
            When ``full_text`` is absent or empty – fast-exit, no API cost.
        LLMAPIError, LLMTimeoutError, ParseError
            Propagated from ``_generate_summary`` on LLM / parsing failures.
        """
        # SM-004 fast-exit guard: avoid spending API tokens on empty transcripts.
        if not transcript.get("full_text", "").strip():
            logger.warning("[SM] Transcript is empty – aborting summarisation.")
            raise EmptyTranscriptError()

        # --- LLM extraction ---
        logger.info("[SM] Starting summarisation pipeline.")
        structured = self._generate_summary(transcript)

        # --- Speaker analytics (two-layer approach) ---
        segments = transcript.get("segments", [])
        speaker_stats: dict | None = None
        text_speaker_analysis: dict | None = None

        # Layer 1: STT audio-based diarisation (pure math, no LLM cost)
        if transcript.get("diarisation_available") and segments:
            logger.info("[SM] Computing speaker analytics from STT diarisation data.")
            speaker_stats = _analyse_participation(segments)
            if speaker_stats:
                speaker_stats["detection_method"] = "stt_diarisation"

        # Layer 2: LLM text-based context analysis (ALWAYS runs when segments exist)
        # This catches cases where STT sees 1 speaker (shared mic) but the text
        # clearly contains multiple participants (e.g. "Hi Ahmed" / "Thanks Fahd").
        if segments:
            logger.info(
                "[SM] Running LLM-based text speaker analysis (context detection)."
            )
            enriched_segments = self._detect_speakers_from_text(transcript)
            text_speaker_analysis = _analyse_participation(enriched_segments)
            if text_speaker_analysis:
                text_speaker_analysis["detection_method"] = "llm_inferred"
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
