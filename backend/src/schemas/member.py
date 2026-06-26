from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateMemberRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    team_id: str


class UpdateMemberRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None


class MemberResponse(BaseModel):
    id: str
    name: str
    email: str
    team_id: str
    company_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
