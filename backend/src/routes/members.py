from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.member_controller import (
    create_member,
    delete_member,
    list_members,
    update_member,
)
from src.helpers.db import get_db
from src.helpers.security import get_current_user
from src.models.user import User
from src.schemas.member import CreateMemberRequest, MemberResponse, UpdateMemberRequest

members_router = APIRouter(prefix="/members", tags=["members"])


@members_router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    request: CreateMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_member(db, current_user, request)


@members_router.get("", response_model=list[MemberResponse])
async def list_all(
    team_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_members(db, current_user, team_id)


@members_router.put("/{member_id}", response_model=MemberResponse)
async def update(
    member_id: str,
    request: UpdateMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_member(db, current_user, member_id, request)


@members_router.delete("/{member_id}")
async def delete(
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await delete_member(db, current_user, member_id)
