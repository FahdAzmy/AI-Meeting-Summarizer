"""Internal implementation package for :mod:`modules.summarisation`."""

from modules._summarisation.analytics import analyse_participation
from modules._summarisation.schemas import (
    ActionItem,
    MeetingReportSchema,
    SpeakerDetectionSchema,
    SpeakerTurn,
)
from modules._summarisation.service import Summarisation

__all__ = [
    "ActionItem",
    "MeetingReportSchema",
    "SpeakerDetectionSchema",
    "SpeakerTurn",
    "Summarisation",
    "analyse_participation",
]
