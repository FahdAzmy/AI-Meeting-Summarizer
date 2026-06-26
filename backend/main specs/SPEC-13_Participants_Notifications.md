# SPEC-13: Meeting Participants & Email Notifications

| Field            | Details                                                    |
|------------------|------------------------------------------------------------|
| **Scope**        | Team-based participant selection + In-server email invites |
| **Files**        | `src/schemas/meeting.py`, `src/services/email_service.py`, `src/routes/notifications.py`, `src/routes/api.py`, `src/orchestrator.py`, `src/routes/export.py` |
| **Traceability** | Phases 5 & 6 — Meeting Participants + Email Notifications  |
| **Framework**    | FastAPI + SQLAlchemy + fastapi-mail/aiosmtplib             |
| **Depends On**   | SPEC-10 (MeetingTeam, MeetingParticipant), SPEC-11 (Auth), SPEC-12 (Teams, Members) |
| **Version**      | 1.0                                                        |
| **Date**         | June 17, 2026                                              |

---

## 13.1 Objective

**Participant Selection**: Replace manual email entry with team/member-based selection. Users choose one or more Teams and/or individual Members — participant emails are resolved automatically.

**Email Notifications**: HR and Team Leaders can send meeting invitations containing title, time, and link. Emails sent asynchronously via `asyncio.create_task()` using the existing SMTP config.

---

## 13.2 Test Plan (TDD)

### T13.01 — Participant Resolution

```python
# tests/unit/test_participant_resolution.py
async def test_resolve_team_to_member_emails(db_session, sample_team_with_members):
    """Selecting a team should resolve to all member emails."""
    from src.services.participant_service import resolve_participants
    emails = await resolve_participants(
        db=db_session,
        team_ids=[sample_team_with_members.id],
        member_ids=[],
        company_id=sample_team_with_members.company_id,
    )
    assert len(emails) == 3  # team has 3 members
    assert all("@" in e for e in emails)

async def test_resolve_individual_members(db_session, sample_members):
    """Selecting individual members returns their emails."""
    from src.services.participant_service import resolve_participants
    emails = await resolve_participants(
        db=db_session, team_ids=[],
        member_ids=[sample_members[0].id],
        company_id=sample_members[0].company_id,
    )
    assert len(emails) == 1

async def test_resolve_deduplicates_emails(db_session, sample_team, member_in_team):
    """If member is selected individually AND via team, email appears once."""
    from src.services.participant_service import resolve_participants
    emails = await resolve_participants(
        db=db_session,
        team_ids=[sample_team.id],
        member_ids=[member_in_team.id],
        company_id=sample_team.company_id,
    )
    assert len(emails) == len(set(emails))

async def test_resolve_rejects_cross_company(db_session, company_a, company_b_team):
    """Teams from another company should be ignored."""
    from src.services.participant_service import resolve_participants
    emails = await resolve_participants(
        db=db_session,
        team_ids=[company_b_team.id],
        member_ids=[], company_id=company_a.id,
    )
    assert len(emails) == 0
```

### T13.02 — Trigger with Teams

```python
# tests/unit/test_trigger_with_teams.py
async def test_trigger_accepts_team_ids(async_client, hr_auth_headers, sample_team):
    r = await async_client.post("/api/trigger", json={
        "meeting_link": "https://meet.google.com/abc",
        "team_ids": [str(sample_team.id)],
    }, headers=hr_auth_headers)
    assert r.status_code == 202
    assert "session_id" in r.json()

async def test_trigger_accepts_member_ids(async_client, hr_auth_headers, sample_member):
    r = await async_client.post("/api/trigger", json={
        "meeting_link": "https://meet.google.com/abc",
        "member_ids": [str(sample_member.id)],
    }, headers=hr_auth_headers)
    assert r.status_code == 202

async def test_trigger_requires_auth(async_client):
    r = await async_client.post("/api/trigger", json={
        "meeting_link": "https://meet.google.com/abc",
    })
    assert r.status_code in (401, 403)
```

### T13.03 — Meeting Scoping

```python
# tests/unit/test_meeting_scoping.py
async def test_meetings_scoped_by_company(async_client, hr_a_headers, hr_b_headers, meeting_a):
    """Company A user should see their meetings, not Company B's."""
    r = await async_client.get("/api/meetings", headers=hr_a_headers)
    assert r.status_code == 200
    ids = [m["id"] for m in r.json()]
    assert str(meeting_a.id) in ids

    r = await async_client.get("/api/meetings", headers=hr_b_headers)
    assert str(meeting_a.id) not in [m["id"] for m in r.json()]

async def test_meeting_detail_404_for_other_company(async_client, hr_b_headers, meeting_a):
    r = await async_client.get(f"/api/meetings/{meeting_a.id}", headers=hr_b_headers)
    assert r.status_code == 404
```

### T13.04 — Email Invitation

```python
# tests/unit/test_email_notifications.py
async def test_send_invitation_endpoint(async_client, hr_auth_headers, sample_meeting, mocker):
    """POST /api/meetings/{id}/invite should send emails to participants."""
    mock_send = mocker.patch("src.services.email_service.send_meeting_invitation")
    r = await async_client.post(
        f"/api/meetings/{sample_meeting.id}/invite",
        headers=hr_auth_headers,
    )
    assert r.status_code == 200
    mock_send.assert_called_once()

async def test_invitation_email_content(mocker):
    """Invitation email should contain title, time, and link."""
    from src.services.email_service import build_invitation_html
    html = build_invitation_html(
        title="Sprint Planning", link="https://meet.google.com/abc",
        scheduled_time="2026-06-20 10:00 UTC",
    )
    assert "Sprint Planning" in html
    assert "https://meet.google.com/abc" in html
    assert "2026-06-20" in html

async def test_invite_requires_auth(async_client, sample_meeting):
    r = await async_client.post(f"/api/meetings/{sample_meeting.id}/invite")
    assert r.status_code in (401, 403)

async def test_invite_404_for_other_company(async_client, hr_b_headers, meeting_a):
    r = await async_client.post(f"/api/meetings/{meeting_a.id}/invite", headers=hr_b_headers)
    assert r.status_code == 404
```

---

## 13.3 Schemas

```python
# src/schemas/meeting.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class CreateMeetingRequest(BaseModel):
    meeting_link: str
    title: str | None = None
    team_ids: list[str] = Field(default_factory=list)
    member_ids: list[str] = Field(default_factory=list)
    scheduled_time: datetime | None = None
    storage: str = "email"

class MeetingResponse(BaseModel):
    id: str; title: str | None; meeting_link: str | None
    platform: str | None; status: str; created_at: datetime
    duration_minutes: int | None; summary: str | None
    action_items: list | None; decisions: list | None
    participants: list[dict] = []  # resolved participant info
```

---

## 13.4 Participant Resolution Service

```python
# src/services/participant_service.py
async def resolve_participants(db, team_ids, member_ids, company_id) -> list[str]:
    """Resolve team_ids + member_ids into deduplicated email list.
    
    1. Query members WHERE team_id IN team_ids AND company_id = company_id
    2. Query members WHERE id IN member_ids AND company_id = company_id
    3. Union and deduplicate by email
    """
    emails = set()
    if team_ids:
        result = await db.execute(
            select(Member.email)
            .where(Member.team_id.in_(team_ids))
            .where(Member.company_id == company_id)
        )
        emails.update(r[0] for r in result.all())
    if member_ids:
        result = await db.execute(
            select(Member.email)
            .where(Member.id.in_(member_ids))
            .where(Member.company_id == company_id)
        )
        emails.update(r[0] for r in result.all())
    return list(emails)
```

---

## 13.5 Email Service

```python
# src/services/email_service.py
import asyncio, aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_meeting_invitation(meeting, participant_emails, settings):
    """Fire-and-forget email invitation to all participants."""
    for email in participant_emails:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Meeting Invitation: {meeting.title or 'Upcoming Meeting'}"
            msg["From"] = settings.MAIL_USERNAME
            msg["To"] = email
            html = build_invitation_html(
                title=meeting.title, link=meeting.meeting_link,
                scheduled_time=str(meeting.scheduled_time),
            )
            msg.attach(MIMEText(html, "html"))
            await aiosmtplib.send(msg,
                hostname=settings.MAIL_SERVER, port=settings.MAIL_PORT,
                username=settings.MAIL_USERNAME, password=settings.MAIL_PASSWORD,
                start_tls=True,
            )
        except Exception as e:
            logger.warning(f"Invitation to {email} failed: {e}")

def build_invitation_html(title, link, scheduled_time):
    """Build HTML email body with meeting title, time, and link."""
    return f"""
    <h2>Meeting Invitation</h2>
    <p><strong>Title:</strong> {title}</p>
    <p><strong>Time:</strong> {scheduled_time}</p>
    <p><strong>Link:</strong> <a href="{link}">{link}</a></p>
    """
```

---

## 13.6 Modified Endpoints

### POST /trigger (Updated)

Now requires auth. Accepts `team_ids` and `member_ids` instead of raw emails.

```python
@api_router.post("/trigger", status_code=202)
async def trigger_pipeline(request: CreateMeetingRequest, 
                           background_tasks: BackgroundTasks,
                           current_user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    emails = await resolve_participants(db, request.team_ids, request.member_ids, current_user.company_id)
    # ... launch pipeline with company_id + created_by
```

### GET /meetings (Updated)

Scoped by `company_id` from JWT:

```python
@api_router.get("/meetings")
async def list_meetings(current_user = Depends(get_current_user), db = Depends(get_db)):
    result = await db.execute(
        select(Meeting).where(Meeting.company_id == current_user.company_id)
        .order_by(Meeting.created_at.desc())
    )
    return [...]
```

### POST /meetings/{id}/invite (New)

```python
@notifications_router.post("/meetings/{id}/invite")
async def send_invite(id: str, current_user = Depends(get_current_user), db = Depends(get_db)):
    meeting = await get_meeting_scoped(db, id, current_user.company_id)
    emails = await resolve_meeting_participants(db, meeting.id)
    asyncio.create_task(send_meeting_invitation(meeting, emails, settings))
    return {"message": "Invitations are being sent", "recipients": len(emails)}
```

---

## 13.7 API Routes Summary

| Method | Endpoint                    | Auth | Description                    |
|--------|-----------------------------|------|--------------------------------|
| POST   | `/api/trigger`              | Yes  | Launch pipeline (team-based)   |
| GET    | `/api/meetings`             | Yes  | List meetings (company-scoped) |
| GET    | `/api/meetings/{id}`        | Yes  | Meeting detail (company-scoped)|
| POST   | `/api/meetings/{id}/invite` | Yes  | Send email invitations         |
| GET    | `/api/export/meetings/excel`| Yes  | Export (company-scoped)        |

---

## 13.8 Acceptance Criteria

| #  | Criteria                                                         | Verified |
|----|------------------------------------------------------------------|----------|
| 1  | Selecting team_ids resolves to member emails                    | ☐        |
| 2  | Selecting member_ids resolves to their emails                   | ☐        |
| 3  | Duplicate emails are deduplicated                               | ☐        |
| 4  | Cross-company teams/members are rejected                        | ☐        |
| 5  | POST /trigger requires auth and accepts team_ids/member_ids     | ☐        |
| 6  | GET /meetings scoped by company_id                              | ☐        |
| 7  | POST /meetings/{id}/invite sends emails via asyncio.create_task | ☐        |
| 8  | Invitation email contains title, time, link                     | ☐        |
| 9  | Export endpoints scoped by company_id                           | ☐        |
| 10 | All T13.01–T13.04 tests pass                                   | ☐        |
