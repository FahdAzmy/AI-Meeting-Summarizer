# src/models/__init__.py
# Import all models so that SQLAlchemy's metadata is fully populated
# before Base.metadata.create_all() is called during init_db().
from src.models.base import Base
from src.models.company import Company
from src.models.user import User, UserRole
from src.models.team import Team
from src.models.member import Member
from src.models.meeting import Meeting, MeetingStatus
from src.models.meeting_team import MeetingTeam
from src.models.meeting_participant import MeetingParticipant

__all__ = [
    "Base",
    "Company",
    "User",
    "UserRole",
    "Team",
    "Member",
    "Meeting",
    "MeetingStatus",
    "MeetingTeam",
    "MeetingParticipant",
]
