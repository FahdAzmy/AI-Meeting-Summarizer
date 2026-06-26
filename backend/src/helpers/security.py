"""
Security utilities for password hashing, JWTs, and RBAC dependencies.
Uses bcrypt directly for compatibility with newer bcrypt versions.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.helpers.config import settings
from src.helpers.db import get_db
from src.helpers.logging_config import get_logger
from src.models.user import User, UserRole

logger = get_logger("auth.security")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def generate_verification_code() -> str:
    """Generate a 6-digit verification code for email verification."""
    return str(secrets.randbelow(900000) + 100000)


def _role_value(role: str | UserRole) -> str:
    return role.value if isinstance(role, UserRole) else str(role)


def _auth_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


def generate_access_token(
    user_id: str | int,
    role: str | UserRole,
    company_id: str | int,
) -> str:
    """Generate a short-lived access token containing tenant and role claims."""
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": str(user_id),
        "role": _role_value(role),
        "company_id": str(company_id),
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    logger.info(
        "Access token generated for user_id=%s, expires_in=%d min",
        user_id,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def generate_refresh_token(user_id: str | int) -> str:
    """Generate a long-lived refresh token with a unique token ID."""
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": str(user_id),
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": now,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    logger.info(
        "Refresh token generated for user_id=%s, expires_in=%d days",
        user_id,
        settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    return jwt.encode(payload, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_access_token(token: str) -> Dict:
    """Verify and decode an access token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "access":
            logger.warning("Access token verification failed: wrong token type")
            raise _auth_error(401, "AUTH-004", "Invalid token type")
        logger.info("Access token verified for user_id=%s", payload.get("user_id"))
        return payload
    except ExpiredSignatureError:
        logger.warning("Access token verification failed: token expired")
        raise _auth_error(401, "AUTH-003", "Token has expired")
    except JWTError:
        logger.warning("Access token verification failed: invalid token")
        raise _auth_error(401, "AUTH-004", "Invalid token")


def verify_refresh_token(token: str) -> Dict:
    """Verify and decode a refresh token."""
    try:
        payload = jwt.decode(
            token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            logger.warning("Refresh token verification failed: wrong token type")
            raise _auth_error(401, "AUTH-004", "Invalid token type")
        logger.info("Refresh token verified for user_id=%s", payload.get("user_id"))
        return payload
    except ExpiredSignatureError:
        logger.warning("Refresh token verification failed: token expired")
        raise _auth_error(401, "AUTH-003", "Refresh token has expired")
    except JWTError:
        logger.warning("Refresh token verification failed: invalid token")
        raise _auth_error(401, "AUTH-004", "Invalid refresh token")


security = HTTPBearer()


async def get_current_user(
    credentials=Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a bearer access token."""
    payload = verify_access_token(credentials.credentials)
    user_id = payload.get("user_id")
    if not user_id:
        logger.warning("get_current_user: token missing user_id")
        raise _auth_error(401, "AUTH-004", "Invalid token: missing user_id")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("get_current_user: user not found for user_id=%s", user_id)
        raise _auth_error(status.HTTP_404_NOT_FOUND, "AUTH-006", "User not found")

    logger.info("Authenticated user_id=%s", user_id)
    return user


def require_role(*allowed_roles: str | UserRole):
    """Dependency factory that allows only users with one of the given roles."""
    allowed = {_role_value(role) for role in allowed_roles}

    async def dep(current_user: User = Depends(get_current_user)) -> User:
        if _role_value(current_user.role) not in allowed:
            raise _auth_error(403, "AUTH-005", "Insufficient permissions")
        return current_user

    return Depends(dep)
