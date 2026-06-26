from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.member import MemberResponse


class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class UpdateTeamRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class AssignLeaderRequest(BaseModel):
    user_id: str


class TeamResponse(BaseModel):
    id: str
    name: str
    leader_id: str | None = None
    leader_email: str | None = None
    company_id: str
    created_at: datetime
    members_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TeamDetailResponse(TeamResponse):
    members: list[MemberResponse] = Field(default_factory=list)
