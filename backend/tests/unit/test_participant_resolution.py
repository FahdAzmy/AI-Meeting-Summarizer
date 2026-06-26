import pytest


@pytest.mark.asyncio
async def test_resolve_team_to_member_emails(db_session, sample_team_with_members):
    from src.services.participant_service import resolve_participants

    emails = await resolve_participants(
        db=db_session,
        team_ids=[sample_team_with_members.id],
        member_ids=[],
        company_id=sample_team_with_members.company_id,
    )
    assert len(emails) == 3
    assert all("@" in email for email in emails)


@pytest.mark.asyncio
async def test_resolve_individual_members(db_session, sample_members):
    from src.services.participant_service import resolve_participants

    emails = await resolve_participants(
        db=db_session,
        team_ids=[],
        member_ids=[sample_members[0].id],
        company_id=sample_members[0].company_id,
    )
    assert emails == [sample_members[0].email]


@pytest.mark.asyncio
async def test_resolve_deduplicates_emails(db_session, sample_team, member_in_team):
    from src.services.participant_service import resolve_participants

    emails = await resolve_participants(
        db=db_session,
        team_ids=[sample_team.id],
        member_ids=[member_in_team.id],
        company_id=sample_team.company_id,
    )
    assert len(emails) == len(set(emails))


@pytest.mark.asyncio
async def test_resolve_rejects_cross_company(db_session, company_a, company_b_team):
    from src.services.participant_service import resolve_participants

    emails = await resolve_participants(
        db=db_session,
        team_ids=[company_b_team.id],
        member_ids=[],
        company_id=company_a.id,
    )
    assert len(emails) == 0
