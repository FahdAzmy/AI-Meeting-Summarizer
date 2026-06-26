import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.member import Member
from src.models.team import Team
from src.models.user import User, UserRole
from src.schemas.team import AssignLeaderRequest, CreateTeamRequest, UpdateTeamRequest


def _parse_uuid(value: str, field: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field} format",
        )


def _role_value(role: str | UserRole) -> str:
    return role.value if isinstance(role, UserRole) else str(role)


def _is_team_leader(user: User) -> bool:
    return _role_value(user.role) == UserRole.TEAM_LEADER.value


async def _team_members_count(db: AsyncSession, team_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count(Member.id)).where(Member.team_id == team_id)
    )
    return int(result.scalar_one())


async def _team_response(db: AsyncSession, team: Team) -> dict:
    leader_email = None
    if team.leader_id:
        result = await db.execute(
            select(User.email).where(User.id == team.leader_id)
        )
        leader_email = result.scalar_one_or_none()

    return {
        "id": str(team.id),
        "name": team.name,
        "leader_id": str(team.leader_id) if team.leader_id else None,
        "leader_email": leader_email,
        "company_id": str(team.company_id),
        "created_at": team.created_at,
        "members_count": await _team_members_count(db, team.id),
    }


async def _get_company_team(
    db: AsyncSession,
    team_id: str,
    company_id: uuid.UUID,
) -> Team:
    parsed_team_id = _parse_uuid(team_id)
    result = await db.execute(
        select(Team).where(
            Team.id == parsed_team_id,
            Team.company_id == company_id,
        )
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    return team


def _ensure_can_view_team(user: User, team: Team) -> None:
    if _is_team_leader(user) and team.leader_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access this team",
        )


async def create_team(
    db: AsyncSession,
    user: User,
    request: CreateTeamRequest,
) -> dict:
    team = Team(name=request.name, company_id=user.company_id)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return await _team_response(db, team)


async def list_teams(db: AsyncSession, user: User) -> list[dict]:
    query = select(Team).where(Team.company_id == user.company_id)
    if _is_team_leader(user):
        query = query.where(Team.leader_id == user.id)
    query = query.order_by(Team.created_at, Team.name)

    result = await db.execute(query)
    teams = result.scalars().all()
    return [await _team_response(db, team) for team in teams]


async def get_team(db: AsyncSession, user: User, team_id: str) -> dict:
    team = await _get_company_team(db, team_id, user.company_id)
    _ensure_can_view_team(user, team)

    result = await db.execute(
        select(Member)
        .where(Member.team_id == team.id, Member.company_id == user.company_id)
        .order_by(Member.created_at, Member.name)
    )
    members = result.scalars().all()
    response = await _team_response(db, team)
    response["members"] = [
        {
            "id": str(member.id),
            "name": member.name,
            "email": member.email,
            "team_id": str(member.team_id),
            "company_id": str(member.company_id),
            "created_at": member.created_at,
        }
        for member in members
    ]
    return response


async def update_team(
    db: AsyncSession,
    user: User,
    team_id: str,
    request: UpdateTeamRequest,
) -> dict:
    team = await _get_company_team(db, team_id, user.company_id)
    updates = request.model_dump(exclude_unset=True)
    if "name" in updates:
        team.name = updates["name"]

    await db.commit()
    await db.refresh(team)
    return await _team_response(db, team)


async def delete_team(db: AsyncSession, user: User, team_id: str) -> dict[str, str]:
    team = await _get_company_team(db, team_id, user.company_id)
    await db.delete(team)
    await db.commit()
    return {"message": "Team deleted"}


async def assign_leader(
    db: AsyncSession,
    user: User,
    team_id: str,
    request: AssignLeaderRequest,
) -> dict:
    team = await _get_company_team(db, team_id, user.company_id)
    target_id = _parse_uuid(request.user_id, "user_id")

    # 1. Try to find a Member with this ID first
    member_result = await db.execute(
        select(Member).where(
            Member.id == target_id,
            Member.company_id == user.company_id,
        )
    )
    member = member_result.scalar_one_or_none()

    leader_user = None
    if member:
        # Check if a User with the member's email already exists
        user_result = await db.execute(
            select(User).where(
                User.email == member.email,
                User.company_id == user.company_id,
            )
        )
        leader_user = user_result.scalar_one_or_none()
        if not leader_user:
            # Create a new team_leader user account for this member
            from src.helpers.security import hash_password
            leader_user = User(
                name=member.name,
                email=member.email,
                password=hash_password("Pass123!"),  # default password
                role=UserRole.TEAM_LEADER,
                company_id=user.company_id,
            )
            db.add(leader_user)
            await db.flush()
        else:
            # Promote/ensure role is team_leader
            if leader_user.role != UserRole.TEAM_LEADER:
                leader_user.role = UserRole.TEAM_LEADER
                await db.flush()
    else:
        # 2. Try to find a User with this ID (for backward compatibility & tests)
        user_result = await db.execute(
            select(User).where(
                User.id == target_id,
                User.company_id == user.company_id,
            )
        )
        leader_user = user_result.scalar_one_or_none()
        if not leader_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leader member or user not found",
            )
        if _role_value(leader_user.role) != UserRole.TEAM_LEADER.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user must have team_leader role",
            )

    team.leader_id = leader_user.id
    await db.commit()
    await db.refresh(team)
    return await _team_response(db, team)
