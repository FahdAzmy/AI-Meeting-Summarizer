import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meeting_participant import MeetingParticipant
from src.models.meeting_team import MeetingTeam
from src.models.member import Member


def _uuid_values(values: list[str | uuid.UUID]) -> list[uuid.UUID]:
    parsed: list[uuid.UUID] = []
    for value in values:
        try:
            parsed.append(value if isinstance(value, uuid.UUID) else uuid.UUID(str(value)))
        except (TypeError, ValueError):
            continue
    return parsed


async def resolve_participants(
    db: AsyncSession,
    team_ids: list[str | uuid.UUID],
    member_ids: list[str | uuid.UUID],
    company_id: str | uuid.UUID,
) -> list[str]:
    """Resolve team and member selections into deduplicated participant emails."""
    emails: set[str] = set()
    company_uuid = company_id if isinstance(company_id, uuid.UUID) else uuid.UUID(str(company_id))
    parsed_team_ids = _uuid_values(team_ids)
    parsed_member_ids = _uuid_values(member_ids)

    if parsed_team_ids:
        result = await db.execute(
            select(Member.email).where(
                Member.team_id.in_(parsed_team_ids),
                Member.company_id == company_uuid,
            )
        )
        emails.update(email for email in result.scalars().all() if email)

    if parsed_member_ids:
        result = await db.execute(
            select(Member.email).where(
                Member.id.in_(parsed_member_ids),
                Member.company_id == company_uuid,
            )
        )
        emails.update(email for email in result.scalars().all() if email)

    return sorted(emails)


async def resolve_meeting_participants(
    db: AsyncSession,
    meeting_id: str | uuid.UUID,
) -> list[str]:
    """Resolve stored meeting participant rows into deduplicated emails."""
    meeting_uuid = meeting_id if isinstance(meeting_id, uuid.UUID) else uuid.UUID(str(meeting_id))
    direct_result = await db.execute(
        select(Member.email)
        .join(MeetingParticipant, MeetingParticipant.member_id == Member.id)
        .where(MeetingParticipant.meeting_id == meeting_uuid)
    )
    team_result = await db.execute(
        select(Member.email)
        .join(MeetingTeam, MeetingTeam.team_id == Member.team_id)
        .where(MeetingTeam.meeting_id == meeting_uuid)
    )
    emails = set(direct_result.scalars().all())
    emails.update(team_result.scalars().all())
    return sorted({email for email in emails if email})
