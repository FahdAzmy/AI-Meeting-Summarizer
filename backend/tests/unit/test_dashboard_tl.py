import pytest


@pytest.mark.asyncio
async def test_tl_dashboard_returns_team_stats(async_client, tl_auth_headers, seeded_data):
    response = await async_client.get("/api/dashboard", headers=tl_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "team_members_count" in data
    assert "meetings_this_month" in data
    assert "pending_action_items" in data


@pytest.mark.asyncio
async def test_tl_sees_only_own_team_stats(
    async_client,
    tl_auth_headers,
    seeded_data,
    other_team_data,
):
    response = await async_client.get("/api/dashboard", headers=tl_auth_headers)
    data = response.json()
    assert data["team_members_count"] == 2
    assert data["team_members_count"] <= seeded_data["members_count"] + other_team_data["total_company_members"]
