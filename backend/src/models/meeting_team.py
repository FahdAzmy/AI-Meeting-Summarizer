# src/models/meeting_team.py
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base


class MeetingTeam(Base):
    __tablename__ = "meeting_teams"

    meeting_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    )
