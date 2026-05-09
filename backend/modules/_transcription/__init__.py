"""Internal implementation package for :mod:`modules.transcription`."""

from modules._transcription.service import Transcription
from modules._transcription.types import TranscriptResult, TranscriptSegment

__all__ = ["TranscriptResult", "TranscriptSegment", "Transcription"]
