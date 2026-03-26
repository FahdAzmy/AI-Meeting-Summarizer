from pydantic import BaseModel, AnyHttpUrl
from typing import List

class JoinMeetingRequest(BaseModel):
    meeting_link: str
    emails: List[str] = []

class JoinMeetingResponse(BaseModel):
    session_id: str

class StatusResponse(BaseModel):
    session_id: str
    status: str
    step: int
    total_steps: int
    message: str
