import pytest


@pytest.mark.asyncio
async def test_hr_can_create_team(async_client, hr_auth_headers):
    response = await async_client.post(
        "/api/teams",
        json={"name": "Backend"},
        headers=hr_auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Backend"


@pytest.mark.asyncio
async def test_hr_can_list_all_teams(async_client, hr_auth_headers, sample_teams):
    response = await async_client.get("/api/teams", headers=hr_auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == len(sample_teams)


@pytest.mark.asyncio
async def test_hr_can_update_team(async_client, hr_auth_headers, sample_team):
    response = await async_client.put(
        f"/api/teams/{sample_team.id}",
        json={"name": "Renamed"},
        headers=hr_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


@pytest.mark.asyncio
async def test_hr_can_delete_team(async_client, hr_auth_headers, sample_team):
    response = await async_client.delete(
        f"/api/teams/{sample_team.id}",
        headers=hr_auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_hr_can_assign_leader(
    async_client,
    hr_auth_headers,
    sample_team,
    sample_tl_user,
):
    response = await async_client.post(
        f"/api/teams/{sample_team.id}/leader",
        json={"user_id": str(sample_tl_user.id)},
        headers=hr_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["leader_id"] == str(sample_tl_user.id)
