import pytest


@pytest.mark.asyncio
async def test_tl_can_add_member_to_own_team(async_client, tl_auth_headers, tl_team):
    response = await async_client.post(
        "/api/members",
        json={
            "name": "New",
            "email": "new@co.com",
            "team_id": str(tl_team.id),
        },
        headers=tl_auth_headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_tl_cannot_add_member_to_other_team(
    async_client,
    tl_auth_headers,
    other_team,
):
    response = await async_client.post(
        "/api/members",
        json={
            "name": "X",
            "email": "x@co.com",
            "team_id": str(other_team.id),
        },
        headers=tl_auth_headers,
    )
    assert response.status_code == 403
