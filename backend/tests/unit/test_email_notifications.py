from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_send_invitation_endpoint(async_client, hr_auth_headers, sample_meeting):
    mock_send = AsyncMock()
    with patch("src.routes.notifications.send_meeting_invitation", mock_send):
        response = await async_client.post(
            f"/api/meetings/{sample_meeting.id}/invite",
            headers=hr_auth_headers,
        )

    assert response.status_code == 200
    mock_send.assert_called_once()


def test_invitation_email_content():
    from src.services.email_service import build_invitation_html

    html = build_invitation_html(
        title="Sprint Planning",
        link="https://meet.google.com/abc",
    )
    assert "Sprint Planning" in html
    assert "https://meet.google.com/abc" in html


@pytest.mark.asyncio
async def test_invite_requires_auth(async_client, sample_meeting):
    response = await async_client.post(f"/api/meetings/{sample_meeting.id}/invite")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_invite_404_for_other_company(async_client, hr_b_headers, meeting_a):
    response = await async_client.post(
        f"/api/meetings/{meeting_a.id}/invite",
        headers=hr_b_headers,
    )
    assert response.status_code == 404
