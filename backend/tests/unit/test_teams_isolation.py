import pytest


@pytest.mark.asyncio
async def test_company_a_cannot_see_company_b_teams(
    async_client,
    hr_a_headers,
    company_b_team,
):
    response = await async_client.get(
        f"/api/teams/{company_b_team.id}",
        headers=hr_a_headers,
    )
    assert response.status_code == 404
