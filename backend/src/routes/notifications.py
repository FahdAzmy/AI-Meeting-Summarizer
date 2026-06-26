import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.config import settings
from src.helpers.db import get_db
from src.helpers.security import get_current_user
from src.models.meeting import Meeting
from src.models.user import User
from src.services.email_service import send_meeting_invitation
from src.services.participant_service import resolve_meeting_participants

notifications_router = APIRouter(tags=["notifications"])


@notifications_router.post("/meetings/{meeting_id}/invite")
async def send_invite(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        parsed_meeting_id = uuid.UUID(meeting_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format",
        )

    result = await db.execute(
        select(Meeting).where(
            Meeting.id == parsed_meeting_id,
            Meeting.company_id == current_user.company_id,
        )
    )
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    emails = await resolve_meeting_participants(db, meeting.id)
    asyncio.create_task(send_meeting_invitation(meeting, emails, settings))
    return {"message": "Invitations are being sent", "recipients": len(emails)}
