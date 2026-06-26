import pytest


@pytest.mark.asyncio
async def test_hr_dashboard_returns_all_stats(async_client, hr_auth_headers, seeded_data):
    response = await async_client.get("/api/dashboard", headers=hr_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_teams" in data
    assert "total_members" in data
    assert "total_meetings" in data
    assert "total_meeting_hours" in data
    assert "most_active_team" in data


@pytest.mark.asyncio
async def test_hr_dashboard_counts_correct(async_client, hr_auth_headers, seeded_data):
    response = await async_client.get("/api/dashboard", headers=hr_auth_headers)
    data = response.json()
    assert data["total_teams"] == seeded_data["teams_count"]
    assert data["total_members"] == seeded_data["members_count"]
    assert data["total_meetings"] == seeded_data["meetings_count"]
    assert data["total_meeting_hours"] == 1.5


@pytest.mark.asyncio
async def test_hr_dashboard_scoped_by_company(
    async_client,
    hr_a_headers,
    hr_b_headers,
    seeded_data,
):
    response_a = await async_client.get("/api/dashboard", headers=hr_a_headers)
    response_b = await async_client.get("/api/dashboard", headers=hr_b_headers)
    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert response_a.json()["total_teams"] != response_b.json()["total_teams"]
