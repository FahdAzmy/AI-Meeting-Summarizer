from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controllers.auth_controller import (
    login_user,
    refresh_access_token,
    register_user,
)
from src.helpers.db import get_db
from src.helpers.security import get_current_user
from src.models.user import User
from src.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

auth_router = APIRouter(prefix="/auth", tags=["auth"])


def _role_value(role) -> str:
    return role.value if hasattr(role, "value") else str(role)


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        role=_role_value(user.role),
        company_id=str(user.company_id),
    )


@auth_router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await register_user(request, db)


@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await login_user(request, db)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_access_token(request, db)


@auth_router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return _to_user_response(current_user)
