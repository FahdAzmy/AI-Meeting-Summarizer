import pytest


@pytest.mark.asyncio
async def test_tl_cannot_create_team(async_client, tl_auth_headers):
    response = await async_client.post(
        "/api/teams",
        json={"name": "T"},
        headers=tl_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tl_cannot_delete_team(async_client, tl_auth_headers, tl_team):
    response = await async_client.delete(
        f"/api/teams/{tl_team.id}",
        headers=tl_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tl_can_view_own_team(async_client, tl_auth_headers, tl_team):
    response = await async_client.get("/api/teams", headers=tl_auth_headers)
    assert response.status_code == 200
    team_ids = [team["id"] for team in response.json()]
    assert str(tl_team.id) in team_ids


@pytest.mark.asyncio
async def test_tl_cannot_view_other_teams(async_client, tl_auth_headers, other_team):
    response = await async_client.get(
        f"/api/teams/{other_team.id}",
        headers=tl_auth_headers,
    )
    assert response.status_code == 403
