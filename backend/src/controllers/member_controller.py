import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.member import Member
from src.models.team import Team
from src.models.user import User, UserRole
from src.schemas.member import CreateMemberRequest, UpdateMemberRequest


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


def _member_response(member: Member) -> dict:
    return {
        "id": str(member.id),
        "name": member.name,
        "email": member.email,
        "team_id": str(member.team_id),
        "company_id": str(member.company_id),
        "created_at": member.created_at,
    }


async def _get_company_team(
    db: AsyncSession,
    team_id: str | uuid.UUID,
    company_id: uuid.UUID,
) -> Team:
    parsed_team_id = (
        team_id if isinstance(team_id, uuid.UUID) else _parse_uuid(team_id, "team_id")
    )
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


async def _get_company_member(
    db: AsyncSession,
    member_id: str,
    company_id: uuid.UUID,
) -> Member:
    parsed_member_id = _parse_uuid(member_id)
    result = await db.execute(
        select(Member).where(
            Member.id == parsed_member_id,
            Member.company_id == company_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    return member


def _ensure_can_manage_team(user: User, team: Team) -> None:
    if _is_team_leader(user) and team.leader_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot manage members outside your team",
        )


async def create_member(
    db: AsyncSession,
    user: User,
    request: CreateMemberRequest,
) -> dict:
    team = await _get_company_team(db, request.team_id, user.company_id)
    _ensure_can_manage_team(user, team)

    member = Member(
        name=request.name,
        email=str(request.email),
        team_id=team.id,
        company_id=user.company_id,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return _member_response(member)


async def list_members(
    db: AsyncSession,
    user: User,
    team_id: str | None = None,
) -> list[dict]:
    query = select(Member).where(Member.company_id == user.company_id)

    if team_id:
        team = await _get_company_team(db, team_id, user.company_id)
        _ensure_can_manage_team(user, team)
        query = query.where(Member.team_id == team.id)
    elif _is_team_leader(user):
        assigned_team_ids = select(Team.id).where(
            Team.company_id == user.company_id,
            Team.leader_id == user.id,
        )
        query = query.where(Member.team_id.in_(assigned_team_ids))

    result = await db.execute(query.order_by(Member.created_at, Member.name))
    return [_member_response(member) for member in result.scalars().all()]


async def update_member(
    db: AsyncSession,
    user: User,
    member_id: str,
    request: UpdateMemberRequest,
) -> dict:
    member = await _get_company_member(db, member_id, user.company_id)
    team = await _get_company_team(db, member.team_id, user.company_id)
    _ensure_can_manage_team(user, team)

    updates = request.model_dump(exclude_unset=True)
    if "name" in updates:
        member.name = updates["name"]
    if "email" in updates:
        member.email = str(updates["email"])

    await db.commit()
    await db.refresh(member)
    return _member_response(member)


async def delete_member(
    db: AsyncSession,
    user: User,
    member_id: str,
) -> dict[str, str]:
    member = await _get_company_member(db, member_id, user.company_id)
    team = await _get_company_team(db, member.team_id, user.company_id)
    _ensure_can_manage_team(user, team)

    await db.delete(member)
    await db.commit()
    return {"message": "Member deleted"}
