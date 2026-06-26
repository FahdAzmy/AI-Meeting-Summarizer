from datetime import datetime

from pydantic import BaseModel, Field


class CreateMeetingRequest(BaseModel):
    meeting_link: str
    title: str | None = None
    team_ids: list[str] = Field(default_factory=list)
    member_ids: list[str] = Field(default_factory=list)
    storage: str = "email"


class MeetingResponse(BaseModel):
    id: str
    title: str | None = None
    meeting_link: str | None = None
    platform: str | None = None
    status: str
    created_at: datetime | None = None
    duration_minutes: int | None = None
    summary: str | None = None
    action_items: list | None = None
    decisions: list | None = None
    participants: list[dict] = Field(default_factory=list)
