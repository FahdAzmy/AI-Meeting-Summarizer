from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.meeting import Meeting, MeetingStatus
from src.models.meeting_team import MeetingTeam
from src.models.member import Member
from src.models.team import Team
from src.models.user import User
from src.schemas.dashboard import HRDashboardResponse, TeamLeaderDashboardResponse


async def _scalar_int(db: AsyncSession, stmt) -> int:
    value = await db.scalar(stmt)
    return int(value or 0)


async def get_hr_dashboard(db: AsyncSession, company_id) -> HRDashboardResponse:
    """Aggregate company-wide dashboard stats for HR users."""
    total_teams = await _scalar_int(
        db, select(func.count(Team.id)).where(Team.company_id == company_id)
    )
    total_members = await _scalar_int(
        db, select(func.count(Member.id)).where(Member.company_id == company_id)
    )
    total_meetings = await _scalar_int(
        db, select(func.count(Meeting.id)).where(Meeting.company_id == company_id)
    )
    duration_minutes = await db.scalar(
        select(func.coalesce(func.sum(Meeting.duration_minutes), 0)).where(
            Meeting.company_id == company_id
        )
    )

    most_active = await db.execute(
        select(Team.name, func.count(MeetingTeam.meeting_id).label("cnt"))
        .join(MeetingTeam, MeetingTeam.team_id == Team.id)
        .where(Team.company_id == company_id)
        .group_by(Team.name)
        .order_by(func.count(MeetingTeam.meeting_id).desc(), Team.name.asc())
        .limit(1)
    )
    row = most_active.first()

    return HRDashboardResponse(
        total_teams=total_teams,
        total_members=total_members,
        total_meetings=total_meetings,
        total_meeting_hours=round(float(duration_minutes or 0) / 60, 1),
        most_active_team=row[0] if row else None,
    )


async def get_tl_dashboard(db: AsyncSession, user: User) -> TeamLeaderDashboardResponse:
    """Aggregate stats for teams led by the current team leader."""
    teams = await db.execute(
        select(Team.id).where(Team.company_id == user.company_id, Team.leader_id == user.id)
    )
    team_ids = [row[0] for row in teams.all()]
    if not team_ids:
        return TeamLeaderDashboardResponse()

    members_count = await _scalar_int(
        db,
        select(func.count(Member.id)).where(
            Member.company_id == user.company_id,
            Member.team_id.in_(team_ids),
        ),
    )

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    meetings_this_month = await _scalar_int(
        db,
        select(func.count(func.distinct(Meeting.id)))
        .join(MeetingTeam, MeetingTeam.meeting_id == Meeting.id)
        .where(
            Meeting.company_id == user.company_id,
            MeetingTeam.team_id.in_(team_ids),
            Meeting.created_at >= month_start,
        ),
    )

    completed = await db.execute(
        select(Meeting.action_items)
        .join(MeetingTeam, MeetingTeam.meeting_id == Meeting.id)
        .where(
            Meeting.company_id == user.company_id,
            MeetingTeam.team_id.in_(team_ids),
            Meeting.status == MeetingStatus.COMPLETED,
        )
    )
    pending_action_items = sum(len(row[0] or []) for row in completed.all())

    return TeamLeaderDashboardResponse(
        team_members_count=members_count,
        meetings_this_month=meetings_this_month,
        pending_action_items=pending_action_items,
    )
