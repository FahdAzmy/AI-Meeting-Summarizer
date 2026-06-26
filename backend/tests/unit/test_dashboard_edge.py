import pytest


@pytest.mark.asyncio
async def test_dashboard_empty_company(async_client, empty_company_hr_headers):
    response = await async_client.get("/api/dashboard", headers=empty_company_hr_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_teams"] == 0
    assert data["total_meetings"] == 0
    assert data["total_meeting_hours"] == 0


@pytest.mark.asyncio
async def test_dashboard_requires_auth(async_client):
    response = await async_client.get("/api/dashboard")
    assert response.status_code in (401, 403)
