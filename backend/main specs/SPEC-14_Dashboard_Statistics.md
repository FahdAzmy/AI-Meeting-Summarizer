# SPEC-14: Dashboard Statistics

| Field            | Details                                                    |
|------------------|------------------------------------------------------------|
| **Scope**        | Role-based dashboard statistics API                        |
| **Files**        | `src/controllers/dashboard_controller.py`, `src/schemas/dashboard.py`, `src/routes/dashboard.py` |
| **Traceability** | Phase 7 — Dashboard Statistics                             |
| **Framework**    | FastAPI + SQLAlchemy                                       |
| **Depends On**   | SPEC-10 (All models), SPEC-11 (Auth/RBAC), SPEC-12 (Teams/Members) |
| **Version**      | 1.0                                                        |
| **Date**         | June 17, 2026                                              |

---

## 14.1 Objective

Provide role-appropriate dashboard statistics for HR and Team Leaders. All queries scoped by `company_id`.

### HR Dashboard
| Metric              | Query                                                      |
|---------------------|-----------------------------------------------------------|
| Total Teams         | `COUNT(*) FROM teams WHERE company_id = ?`                |
| Total Members       | `COUNT(*) FROM members WHERE company_id = ?`              |
| Total Meetings      | `COUNT(*) FROM meetings WHERE company_id = ?`             |
| Total Meeting Hours | `SUM(duration_minutes) / 60 FROM meetings WHERE company_id = ?` |
| Most Active Team    | JOIN meeting_teams → meetings, GROUP BY team, ORDER BY count DESC |

### Team Leader Dashboard
| Metric              | Query                                                      |
|---------------------|-----------------------------------------------------------|
| Team Members Count  | `COUNT(*) FROM members WHERE team_id = ?`                 |
| Meetings This Month | Meetings linked to leader's team(s) in current month      |
| Pending Action Items| From completed meetings linked to leader's team(s)        |

---

## 14.2 Test Plan (TDD)

### T14.01 — HR Dashboard Stats

```python
# tests/unit/test_dashboard_hr.py
async def test_hr_dashboard_returns_all_stats(async_client, hr_auth_headers, seeded_data):
    """GET /api/dashboard should return complete HR stats."""
    r = await async_client.get("/api/dashboard", headers=hr_auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_teams" in data
    assert "total_members" in data
    assert "total_meetings" in data
    assert "total_meeting_hours" in data
    assert "most_active_team" in data

async def test_hr_dashboard_counts_correct(async_client, hr_auth_headers, seeded_data):
    """Stats should match actual seeded data counts."""
    r = await async_client.get("/api/dashboard", headers=hr_auth_headers)
    data = r.json()
    assert data["total_teams"] == seeded_data["teams_count"]
    assert data["total_members"] == seeded_data["members_count"]
    assert data["total_meetings"] == seeded_data["meetings_count"]

async def test_hr_dashboard_scoped_by_company(async_client, hr_a_headers, hr_b_headers):
    """Each company should see only their own stats."""
    r_a = await async_client.get("/api/dashboard", headers=hr_a_headers)
    r_b = await async_client.get("/api/dashboard", headers=hr_b_headers)
    assert r_a.json()["total_teams"] != r_b.json()["total_teams"]
```

### T14.02 — Team Leader Dashboard Stats

```python
# tests/unit/test_dashboard_tl.py
async def test_tl_dashboard_returns_team_stats(async_client, tl_auth_headers, seeded_data):
    """TL dashboard should show team-specific stats."""
    r = await async_client.get("/api/dashboard", headers=tl_auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "team_members_count" in data
    assert "meetings_this_month" in data
    assert "pending_action_items" in data

async def test_tl_sees_only_own_team_stats(async_client, tl_auth_headers, other_team_data):
    """TL should NOT see stats from teams they don't lead."""
    r = await async_client.get("/api/dashboard", headers=tl_auth_headers)
    data = r.json()
    # members count should only reflect leader's team
    assert data["team_members_count"] <= other_team_data["total_company_members"]
```

### T14.03 — Edge Cases

```python
# tests/unit/test_dashboard_edge.py
async def test_dashboard_empty_company(async_client, empty_company_hr_headers):
    """Dashboard with no data should return zeroes, not errors."""
    r = await async_client.get("/api/dashboard", headers=empty_company_hr_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_teams"] == 0
    assert data["total_meetings"] == 0
    assert data["total_meeting_hours"] == 0

async def test_dashboard_requires_auth(async_client):
    """Unauthenticated request should return 401."""
    r = await async_client.get("/api/dashboard")
    assert r.status_code in (401, 403)
```

---

## 14.3 Schemas

```python
# src/schemas/dashboard.py
from pydantic import BaseModel

class HRDashboardResponse(BaseModel):
    total_teams: int = 0
    total_members: int = 0
    total_meetings: int = 0
    total_meeting_hours: float = 0.0
    most_active_team: str | None = None

class TeamLeaderDashboardResponse(BaseModel):
    team_members_count: int = 0
    meetings_this_month: int = 0
    pending_action_items: int = 0
```

---

## 14.4 Controller Logic

```python
# src/controllers/dashboard_controller.py
from sqlalchemy import select, func
from datetime import datetime, timezone

async def get_hr_dashboard(db, company_id):
    """Aggregate stats for HR dashboard."""
    total_teams = await db.scalar(
        select(func.count(Team.id)).where(Team.company_id == company_id)
    )
    total_members = await db.scalar(
        select(func.count(Member.id)).where(Member.company_id == company_id)
    )
    total_meetings = await db.scalar(
        select(func.count(Meeting.id)).where(Meeting.company_id == company_id)
    )
    total_hours = await db.scalar(
        select(func.coalesce(func.sum(Meeting.duration_minutes), 0))
        .where(Meeting.company_id == company_id)
    ) / 60

    # Most active team
    most_active = await db.execute(
        select(Team.name, func.count(MeetingTeam.meeting_id).label("cnt"))
        .join(MeetingTeam, MeetingTeam.team_id == Team.id)
        .where(Team.company_id == company_id)
        .group_by(Team.name).order_by(func.count(MeetingTeam.meeting_id).desc())
        .limit(1)
    )
    row = most_active.first()

    return HRDashboardResponse(
        total_teams=total_teams or 0,
        total_members=total_members or 0,
        total_meetings=total_meetings or 0,
        total_meeting_hours=round(total_hours, 1),
        most_active_team=row[0] if row else None,
    )

async def get_tl_dashboard(db, user):
    """Aggregate stats for Team Leader dashboard."""
    # Get leader's team(s)
    teams = await db.execute(
        select(Team.id).where(Team.leader_id == user.id)
    )
    team_ids = [t[0] for t in teams.all()]

    members_count = await db.scalar(
        select(func.count(Member.id)).where(Member.team_id.in_(team_ids))
    ) if team_ids else 0

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    meetings_month = await db.scalar(
        select(func.count(Meeting.id))
        .join(MeetingTeam, MeetingTeam.meeting_id == Meeting.id)
        .where(MeetingTeam.team_id.in_(team_ids))
        .where(Meeting.created_at >= month_start)
    ) if team_ids else 0

    # Count action items from completed meetings
    completed = await db.execute(
        select(Meeting.action_items)
        .join(MeetingTeam, MeetingTeam.meeting_id == Meeting.id)
        .where(MeetingTeam.team_id.in_(team_ids))
        .where(Meeting.status == MeetingStatus.COMPLETED)
    ) if team_ids else []
    action_count = sum(len(r[0] or []) for r in (completed.all() if team_ids else []))

    return TeamLeaderDashboardResponse(
        team_members_count=members_count or 0,
        meetings_this_month=meetings_month or 0,
        pending_action_items=action_count,
    )
```

---

## 14.5 API Route

| Method | Endpoint         | Auth | Description                         |
|--------|------------------|------|-------------------------------------|
| GET    | `/api/dashboard` | Yes  | HR → HR stats; TL → TL stats       |

```python
# src/routes/dashboard.py
@dashboard_router.get("/dashboard")
async def get_dashboard(current_user = Depends(get_current_user), db = Depends(get_db)):
    if current_user.role == UserRole.HR:
        return await get_hr_dashboard(db, current_user.company_id)
    else:
        return await get_tl_dashboard(db, current_user)
```

---

## 14.6 Acceptance Criteria

| #  | Criteria                                                     | Verified |
|----|--------------------------------------------------------------|----------|
| 1  | HR dashboard returns total_teams, members, meetings, hours  | ☐        |
| 2  | HR dashboard returns most_active_team                       | ☐        |
| 3  | TL dashboard returns team_members_count, meetings_this_month| ☐        |
| 4  | TL dashboard returns pending_action_items count             | ☐        |
| 5  | Stats scoped by company_id (HR)                             | ☐        |
| 6  | Stats scoped by leader's team(s) (TL)                       | ☐        |
| 7  | Empty company returns zeroes, not errors                    | ☐        |
| 8  | Endpoint requires authentication                            | ☐        |
| 9  | All T14.01–T14.03 tests pass                               | ☐        |
