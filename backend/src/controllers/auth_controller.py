from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.security import (
    generate_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from src.models.company import Company
from src.models.user import User, UserRole
from src.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse


def _role_value(role: str | UserRole) -> str:
    return role.value if isinstance(role, UserRole) else str(role)


def _user_payload(user: User) -> dict[str, str]:
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": _role_value(user.role),
        "company_id": str(user.company_id),
    }


def _token_response(user: User, refresh_token: str | None = None) -> TokenResponse:
    return TokenResponse(
        access_token=generate_access_token(user.id, user.role, user.company_id),
        refresh_token=refresh_token or generate_refresh_token(user.id),
        user=_user_payload(user),
    )


def _auth_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


async def register_user(
    request: RegisterRequest,
    db: AsyncSession,
) -> TokenResponse:
    existing_user = await db.execute(select(User).where(User.email == request.email))
    if existing_user.scalar_one_or_none():
        raise _auth_error(
            status.HTTP_409_CONFLICT,
            "AUTH-002",
            "Email is already registered",
        )

    result = await db.execute(select(Company).where(Company.name == request.company_name))
    company = result.scalar_one_or_none()
    if not company:
        company = Company(name=request.company_name)
        db.add(company)
        await db.flush()

    user = User(
        name=request.name,
        email=request.email,
        password=hash_password(request.password),
        role=UserRole.HR,
        company_id=company.id,
    )
    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise _auth_error(
            status.HTTP_409_CONFLICT,
            "AUTH-002",
            "Email is already registered",
        )

    await db.refresh(user)
    return _token_response(user)


async def login_user(request: LoginRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password):
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED,
            "AUTH-001",
            "Wrong email or password",
        )

    return _token_response(user)


async def refresh_access_token(
    request: RefreshRequest,
    db: AsyncSession,
) -> TokenResponse:
    payload = verify_refresh_token(request.refresh_token)
    user_id = payload.get("user_id")
    if not user_id:
        raise _auth_error(
            status.HTTP_401_UNAUTHORIZED,
            "AUTH-004",
            "Invalid refresh token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise _auth_error(status.HTTP_404_NOT_FOUND, "AUTH-006", "User not found")

    return _token_response(user, refresh_token=request.refresh_token)
