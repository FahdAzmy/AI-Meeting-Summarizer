from pydantic import BaseModel


class HRDashboardResponse(BaseModel):
    total_teams: int = 0
    total_members: int = 0
    total_meetings: int = 0
    total_meeting_hours: float = 0.0
    most_active_team: str | None = None


class TeamLeaderDashboardResponse(BaseModel):
    team_members_count: int = 0
    meetings_this_month: int = 0
    pending_action_items: int = 0
