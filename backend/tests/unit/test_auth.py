from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from src.helpers.config import settings
from src.helpers.security import (
    generate_access_token,
    generate_refresh_token,
    hash_password,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)


def test_hash_password_returns_bcrypt_hash():
    hashed = hash_password("myPassword123")
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    hashed = hash_password("secret")
    assert verify_password("secret", hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("secret")
    assert verify_password("wrong", hashed) is False


def test_access_token_contains_user_id_role_company():
    token = generate_access_token(user_id="u1", role="hr", company_id="c1")
    payload = verify_access_token(token)
    assert payload["user_id"] == "u1"
    assert payload["role"] == "hr"
    assert payload["company_id"] == "c1"


def test_refresh_token_contains_jti():
    token = generate_refresh_token(user_id="u1")
    payload = verify_refresh_token(token)
    assert "jti" in payload


def test_expired_token_raises_401():
    expired_token = jwt.encode(
        {
            "user_id": "u1",
            "role": "hr",
            "company_id": "c1",
            "type": "access",
            "iat": datetime.utcnow() - timedelta(hours=2),
            "exp": datetime.utcnow() - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    with pytest.raises(HTTPException):
        verify_access_token(expired_token)


@pytest.mark.asyncio
async def test_register_creates_company_and_hr_user(async_client):
    response = await async_client.post(
        "/api/auth/register",
        json={
            "name": "Ahmed",
            "email": "ahmed@co.com",
            "password": "Pass123!",
            "company_name": "New Co",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["role"] == "hr"


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(async_client):
    payload = {
        "name": "A",
        "email": "dup@t.com",
        "password": "P1!",
        "company_name": "C",
    }
    await async_client.post("/api/auth/register", json=payload)
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_returns_tokens(async_client, registered_user):
    response = await async_client.post(
        "/api/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password_fails(async_client, registered_user):
    response = await async_client.post(
        "/api/auth/login",
        json={"email": registered_user["email"], "password": "Wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_returns_new_access_token(async_client, auth_tokens):
    response = await async_client.post(
        "/api/auth/refresh",
        json={"refresh_token": auth_tokens["refresh_token"]},
    )
    assert response.status_code == 200
    assert response.json()["access_token"] != auth_tokens["access_token"]


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(async_client):
    response = await async_client.get("/api/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_hr_only_route_rejects_team_leader(async_client, tl_auth_headers):
    response = await async_client.post(
        "/api/teams",
        json={"name": "T"},
        headers=tl_auth_headers,
    )
    assert response.status_code == 403
