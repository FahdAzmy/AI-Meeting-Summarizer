import pytest


@pytest.mark.asyncio
async def test_trigger_accepts_team_ids(async_client, hr_auth_headers, sample_team):
    response = await async_client.post(
        "/api/trigger",
        json={
            "meeting_link": "https://meet.google.com/abc",
            "team_ids": [str(sample_team.id)],
        },
        headers=hr_auth_headers,
    )
    assert response.status_code == 202
    assert "session_id" in response.json()


@pytest.mark.asyncio
async def test_trigger_accepts_member_ids(async_client, hr_auth_headers, sample_member):
    response = await async_client.post(
        "/api/trigger",
        json={
            "meeting_link": "https://meet.google.com/abc",
            "member_ids": [str(sample_member.id)],
        },
        headers=hr_auth_headers,
    )
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_trigger_requires_auth(async_client):
    response = await async_client.post(
        "/api/trigger",
        json={"meeting_link": "https://meet.google.com/abc"},
    )
    assert response.status_code in (401, 403)
