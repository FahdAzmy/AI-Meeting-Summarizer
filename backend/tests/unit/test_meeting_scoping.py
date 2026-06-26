import pytest


@pytest.mark.asyncio
async def test_meetings_scoped_by_company(async_client, hr_a_headers, hr_b_headers, meeting_a):
    response = await async_client.get("/api/meetings", headers=hr_a_headers)
    assert response.status_code == 200
    ids = [meeting["id"] for meeting in response.json()]
    assert str(meeting_a.id) in ids

    response = await async_client.get("/api/meetings", headers=hr_b_headers)
    assert response.status_code == 200
    assert str(meeting_a.id) not in [meeting["id"] for meeting in response.json()]


@pytest.mark.asyncio
async def test_meeting_detail_404_for_other_company(async_client, hr_b_headers, meeting_a):
    response = await async_client.get(
        f"/api/meetings/{meeting_a.id}",
        headers=hr_b_headers,
    )
    assert response.status_code == 404
