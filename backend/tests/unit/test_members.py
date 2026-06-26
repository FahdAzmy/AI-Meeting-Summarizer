import pytest


@pytest.mark.asyncio
async def test_add_member_to_team(async_client, hr_auth_headers, sample_team):
    response = await async_client.post(
        "/api/members",
        json={
            "name": "Fahd",
            "email": "fahd@co.com",
            "team_id": str(sample_team.id),
        },
        headers=hr_auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["team_id"] == str(sample_team.id)


@pytest.mark.asyncio
async def test_update_member(async_client, hr_auth_headers, sample_member):
    response = await async_client.put(
        f"/api/members/{sample_member.id}",
        json={"name": "Updated Name"},
        headers=hr_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_member(async_client, hr_auth_headers, sample_member):
    response = await async_client.delete(
        f"/api/members/{sample_member.id}",
        headers=hr_auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_members_by_team(async_client, hr_auth_headers, sample_team):
    response = await async_client.get(
        f"/api/members?team_id={sample_team.id}",
        headers=hr_auth_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
