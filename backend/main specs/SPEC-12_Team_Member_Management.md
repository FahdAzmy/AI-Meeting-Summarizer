# SPEC-12: Team & Member Management

| Field            | Details                                                    |
|------------------|------------------------------------------------------------|
| **Scope**        | CRUD for Teams and Members with RBAC permissions           |
| **Files**        | `src/schemas/team.py`, `src/schemas/member.py`, `src/controllers/team_controller.py`, `src/controllers/member_controller.py`, `src/routes/teams.py`, `src/routes/members.py` |
| **Traceability** | Phase 4 — Team & Member Management                        |
| **Framework**    | FastAPI + SQLAlchemy                                       |
| **Depends On**   | SPEC-10 (Team, Member models), SPEC-11 (RBAC, auth deps)  |
| **Version**      | 1.0                                                        |
| **Date**         | June 17, 2026                                              |

---

## 12.1 Objective

Implement full CRUD for Teams and Members with role-based permissions:

### HR Permissions
- Create / Update / Delete any Team
- Assign Team Leader
- View all Teams in the company

### Team Leader Permissions
- Manage only their assigned Team
- Add / Edit / Delete Members in their team

All queries scoped by `company_id` for tenant isolation.

---

## 12.2 Test Plan (TDD)

### T12.01 — Team CRUD (HR)

```python
# tests/unit/test_teams.py
async def test_hr_can_create_team(async_client, hr_auth_headers):
    r = await async_client.post("/api/teams", json={"name": "Backend"}, headers=hr_auth_headers)
    assert r.status_code == 201
    assert r.json()["name"] == "Backend"

async def test_hr_can_list_all_teams(async_client, hr_auth_headers, sample_teams):
    r = await async_client.get("/api/teams", headers=hr_auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == len(sample_teams)

async def test_hr_can_update_team(async_client, hr_auth_headers, sample_team):
    r = await async_client.put(f"/api/teams/{sample_team.id}", json={"name": "Renamed"}, headers=hr_auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"

async def test_hr_can_delete_team(async_client, hr_auth_headers, sample_team):
    r = await async_client.delete(f"/api/teams/{sample_team.id}", headers=hr_auth_headers)
    assert r.status_code == 200

async def test_hr_can_assign_leader(async_client, hr_auth_headers, sample_team, sample_tl_user):
    r = await async_client.post(
        f"/api/teams/{sample_team.id}/leader",
        json={"user_id": str(sample_tl_user.id)},
        headers=hr_auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["leader_id"] == str(sample_tl_user.id)
```

### T12.02 — Team CRUD (Team Leader Restrictions)

```python
# tests/unit/test_teams_rbac.py
async def test_tl_cannot_create_team(async_client, tl_auth_headers):
    r = await async_client.post("/api/teams", json={"name": "T"}, headers=tl_auth_headers)
    assert r.status_code == 403

async def test_tl_cannot_delete_team(async_client, tl_auth_headers, tl_team):
    r = await async_client.delete(f"/api/teams/{tl_team.id}", headers=tl_auth_headers)
    assert r.status_code == 403

async def test_tl_can_view_own_team(async_client, tl_auth_headers, tl_team):
    r = await async_client.get("/api/teams", headers=tl_auth_headers)
    assert r.status_code == 200
    team_ids = [t["id"] for t in r.json()]
    assert str(tl_team.id) in team_ids

async def test_tl_cannot_view_other_teams(async_client, tl_auth_headers, other_team):
    r = await async_client.get(f"/api/teams/{other_team.id}", headers=tl_auth_headers)
    assert r.status_code == 403
```

### T12.03 — Tenant Isolation

```python
# tests/unit/test_teams_isolation.py
async def test_company_a_cannot_see_company_b_teams(async_client, hr_a_headers, company_b_team):
    r = await async_client.get(f"/api/teams/{company_b_team.id}", headers=hr_a_headers)
    assert r.status_code == 404
```

### T12.04 — Member CRUD

```python
# tests/unit/test_members.py
async def test_add_member_to_team(async_client, hr_auth_headers, sample_team):
    r = await async_client.post("/api/members", json={
        "name": "Fahd", "email": "fahd@co.com", "team_id": str(sample_team.id),
    }, headers=hr_auth_headers)
    assert r.status_code == 201
    assert r.json()["team_id"] == str(sample_team.id)

async def test_update_member(async_client, hr_auth_headers, sample_member):
    r = await async_client.put(f"/api/members/{sample_member.id}",
        json={"name": "Updated Name"}, headers=hr_auth_headers)
    assert r.status_code == 200

async def test_delete_member(async_client, hr_auth_headers, sample_member):
    r = await async_client.delete(f"/api/members/{sample_member.id}", headers=hr_auth_headers)
    assert r.status_code == 200

async def test_list_members_by_team(async_client, hr_auth_headers, sample_team):
    r = await async_client.get(f"/api/members?team_id={sample_team.id}", headers=hr_auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

### T12.05 — TL Member Management

```python
# tests/unit/test_members_tl.py
async def test_tl_can_add_member_to_own_team(async_client, tl_auth_headers, tl_team):
    r = await async_client.post("/api/members", json={
        "name": "New", "email": "new@co.com", "team_id": str(tl_team.id),
    }, headers=tl_auth_headers)
    assert r.status_code == 201

async def test_tl_cannot_add_member_to_other_team(async_client, tl_auth_headers, other_team):
    r = await async_client.post("/api/members", json={
        "name": "X", "email": "x@co.com", "team_id": str(other_team.id),
    }, headers=tl_auth_headers)
    assert r.status_code == 403
```

---

## 12.3 Schemas

```python
# src/schemas/team.py
class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class UpdateTeamRequest(BaseModel):
    name: str | None = None

class AssignLeaderRequest(BaseModel):
    user_id: str  # UUID of user with team_leader role

class TeamResponse(BaseModel):
    id: str; name: str; leader_id: str | None
    company_id: str; created_at: datetime; members_count: int = 0

# src/schemas/member.py
class CreateMemberRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    team_id: str  # UUID of target team

class UpdateMemberRequest(BaseModel):
    name: str | None = None; email: EmailStr | None = None

class MemberResponse(BaseModel):
    id: str; name: str; email: str
    team_id: str; company_id: str; created_at: datetime
```

---

## 12.4 API Routes

### Teams

| Method | Endpoint                  | Role     | Description               |
|--------|---------------------------|----------|---------------------------|
| POST   | `/api/teams`              | HR only  | Create team               |
| GET    | `/api/teams`              | Any auth | HR: all; TL: own teams    |
| GET    | `/api/teams/{id}`         | Any auth | Team detail + members     |
| PUT    | `/api/teams/{id}`         | HR only  | Update team name          |
| DELETE | `/api/teams/{id}`         | HR only  | Delete team + cascade     |
| POST   | `/api/teams/{id}/leader`  | HR only  | Assign team leader        |

### Members

| Method | Endpoint                  | Role        | Description             |
|--------|---------------------------|-------------|-------------------------|
| POST   | `/api/members`            | HR or TL*   | Add member to team      |
| GET    | `/api/members?team_id=`   | Any auth    | List members by team    |
| PUT    | `/api/members/{id}`       | HR or TL*   | Update member           |
| DELETE | `/api/members/{id}`       | HR or TL*   | Delete member           |

*TL can only manage members of their own team.

---

## 12.5 Controller Logic (company_id Scoping)

```python
# src/controllers/team_controller.py — key pattern
async def list_teams(db, user):
    """HR sees all company teams; TL sees only assigned teams."""
    query = select(Team).where(Team.company_id == user.company_id)
    if user.role == UserRole.TEAM_LEADER:
        query = query.where(Team.leader_id == user.id)
    result = await db.execute(query)
    return result.scalars().all()
```

---

## 12.6 Acceptance Criteria

| #  | Criteria                                                    | Verified |
|----|-------------------------------------------------------------|----------|
| 1  | HR can create, update, delete teams                        | ☐        |
| 2  | HR can assign a team leader                                | ☐        |
| 3  | HR can view all teams in their company                     | ☐        |
| 4  | TL can only view their assigned team(s)                    | ☐        |
| 5  | TL cannot create/update/delete teams                       | ☐        |
| 6  | TL can add/edit/delete members in own team only            | ☐        |
| 7  | Company A cannot see Company B teams                       | ☐        |
| 8  | Deleting a team cascades to members                        | ☐        |
| 9  | All T12.01–T12.05 tests pass                              | ☐        |
