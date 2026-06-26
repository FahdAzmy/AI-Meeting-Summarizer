from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.team_controller import (
    assign_leader,
    create_team,
    delete_team,
    get_team,
    list_teams,
    update_team,
)
from src.helpers.db import get_db
from src.helpers.security import get_current_user, require_role
from src.models.user import User, UserRole
from src.schemas.team import (
    AssignLeaderRequest,
    CreateTeamRequest,
    TeamDetailResponse,
    TeamResponse,
    UpdateTeamRequest,
)

teams_router = APIRouter(prefix="/teams", tags=["teams"])


@teams_router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    request: CreateTeamRequest,
    current_user: User = require_role(UserRole.HR),
    db: AsyncSession = Depends(get_db),
):
    return await create_team(db, current_user, request)


@teams_router.get("", response_model=list[TeamResponse])
async def list_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_teams(db, current_user)


@teams_router.get("/{team_id}", response_model=TeamDetailResponse)
async def detail(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_team(db, current_user, team_id)


@teams_router.put("/{team_id}", response_model=TeamResponse)
async def update(
    team_id: str,
    request: UpdateTeamRequest,
    current_user: User = require_role(UserRole.HR),
    db: AsyncSession = Depends(get_db),
):
    return await update_team(db, current_user, team_id, request)


@teams_router.delete("/{team_id}")
async def delete(
    team_id: str,
    current_user: User = require_role(UserRole.HR),
    db: AsyncSession = Depends(get_db),
):
    return await delete_team(db, current_user, team_id)


@teams_router.post("/{team_id}/leader", response_model=TeamResponse)
async def leader(
    team_id: str,
    request: AssignLeaderRequest,
    current_user: User = require_role(UserRole.HR),
    db: AsyncSession = Depends(get_db),
):
    return await assign_leader(db, current_user, team_id, request)
