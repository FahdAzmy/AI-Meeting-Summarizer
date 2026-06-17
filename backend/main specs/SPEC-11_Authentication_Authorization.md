# SPEC-11: Authentication & Authorization (RBAC)

| Field            | Details                                                    |
|------------------|------------------------------------------------------------|
| **Scope**        | JWT Authentication, Refresh Tokens, Role-Based Access Control |
| **Files**        | `src/helpers/security.py`, `src/schemas/auth.py`, `src/controllers/auth_controller.py`, `src/routes/auth.py` |
| **Traceability** | Phase 3 — Authentication & Authorization                   |
| **Framework**    | FastAPI + python-jose (JWT) + bcrypt                       |
| **Depends On**   | SPEC-10 (User model, Company model)                        |
| **Version**      | 1.0                                                        |
| **Date**         | June 17, 2026                                              |

---

## 11.1 Objective

Build a complete authentication and authorization system with:
- **JWT Access Tokens** (short-lived, 30 min) for API authentication
- **JWT Refresh Tokens** (long-lived, 7 days) for token renewal
- **Password Hashing** via bcrypt (already scaffolded in `security.py`)
- **RBAC** with two roles: `hr` (full admin) and `team_leader` (scoped access)
- **Tenant isolation** — JWT payload includes `company_id`

---

## 11.2 Test Plan (TDD)

### T11.01 — Password Hashing

```python
# tests/unit/test_password_hashing.py
def test_hash_password_returns_bcrypt_hash():
    hashed = hash_password("myPassword123")
    assert hashed.startswith("$2b$")

def test_verify_password_correct():
    hashed = hash_password("secret")
    assert verify_password("secret", hashed) is True

def test_verify_password_incorrect():
    hashed = hash_password("secret")
    assert verify_password("wrong", hashed) is False
```

### T11.02 — Token Generation & Verification

```python
# tests/unit/test_tokens.py
def test_access_token_contains_user_id_role_company():
    token = generate_access_token(user_id="u1", role="hr", company_id="c1")
    payload = verify_access_token(token)
    assert payload["user_id"] == "u1"
    assert payload["role"] == "hr"
    assert payload["company_id"] == "c1"

def test_refresh_token_contains_jti():
    token = generate_refresh_token(user_id="u1")
    payload = verify_refresh_token(token)
    assert "jti" in payload

def test_expired_token_raises_401():
    # Create a token already expired
    with pytest.raises(HTTPException):
        verify_access_token(expired_token)
```

### T11.03 — Registration Endpoint

```python
# tests/unit/test_auth_register.py
async def test_register_creates_company_and_hr_user(async_client, test_db):
    response = await async_client.post("/api/auth/register", json={
        "name": "Ahmed", "email": "ahmed@co.com",
        "password": "Pass123!", "company_name": "New Co",
    })
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert response.json()["user"]["role"] == "hr"

async def test_register_duplicate_email_fails(async_client, test_db):
    payload = {"name": "A", "email": "dup@t.com", "password": "P1!", "company_name": "C"}
    await async_client.post("/api/auth/register", json=payload)
    r = await async_client.post("/api/auth/register", json=payload)
    assert r.status_code == 409
```

### T11.04 — Login Endpoint

```python
# tests/unit/test_auth_login.py
async def test_login_returns_tokens(async_client, registered_user):
    r = await async_client.post("/api/auth/login", json={
        "email": registered_user["email"], "password": registered_user["password"],
    })
    assert r.status_code == 200
    assert "access_token" in r.json()

async def test_login_wrong_password_fails(async_client, registered_user):
    r = await async_client.post("/api/auth/login", json={
        "email": registered_user["email"], "password": "Wrong",
    })
    assert r.status_code == 401
```

### T11.05 — Token Refresh

```python
# tests/unit/test_auth_refresh.py
async def test_refresh_returns_new_access_token(async_client, auth_tokens):
    r = await async_client.post("/api/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"],
    })
    assert r.status_code == 200
    assert r.json()["access_token"] != auth_tokens["access_token"]
```

### T11.06 — RBAC

```python
# tests/unit/test_auth_rbac.py
async def test_unauthenticated_returns_401(async_client):
    r = await async_client.get("/api/auth/me")
    assert r.status_code in (401, 403)

async def test_hr_only_route_rejects_team_leader(async_client, tl_auth_headers):
    r = await async_client.post("/api/teams", json={"name": "T"}, headers=tl_auth_headers)
    assert r.status_code == 403
```

---

## 11.3 Schemas

```python
# src/schemas/auth.py
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)
    company_name: str = Field(..., min_length=2, max_length=255)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str; name: str; email: str; role: str; company_id: str

class TokenResponse(BaseModel):
    access_token: str; refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
```

---

## 11.4 JWT Payload

**Access Token:** `{user_id, role, company_id, exp, iat, type: "access"}`

**Refresh Token:** `{user_id, exp, iat, type: "refresh", jti: "unique-uuid"}`

---

## 11.5 Security Dependencies

```python
# Key additions to src/helpers/security.py
def generate_access_token(user_id, role, company_id) -> str:
    """Include role + company_id in JWT payload."""

def require_role(*allowed_roles):
    """Dependency factory — returns Depends() that checks user.role."""
    async def dep(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return Depends(dep)
```

---

## 11.6 API Routes

| Method | Endpoint              | Auth | Description                     |
|--------|-----------------------|------|---------------------------------|
| POST   | `/api/auth/register`  | No   | Create company + HR user        |
| POST   | `/api/auth/login`     | No   | Validate credentials → tokens   |
| POST   | `/api/auth/refresh`   | No   | New access token from refresh   |
| GET    | `/api/auth/me`        | Yes  | Current user profile            |

---

## 11.7 Registration Flow

```
POST /api/auth/register {name, email, password, company_name}
  → Check email uniqueness
  → Create Company (or find existing)
  → Hash password (bcrypt)
  → Create User (role=hr)
  → Generate access + refresh tokens
  → Return 201 {access_token, refresh_token, user}
```

---

## 11.8 Error Codes

| Code     | HTTP | Trigger                          |
|----------|------|----------------------------------|
| AUTH-001 | 401  | Wrong email or password          |
| AUTH-002 | 409  | Duplicate email on registration  |
| AUTH-003 | 401  | Token expired                    |
| AUTH-004 | 401  | Malformed JWT                    |
| AUTH-005 | 403  | Role not in allowed roles        |
| AUTH-006 | 404  | Token valid but user deleted     |

---

## 11.9 Acceptance Criteria

| #  | Criteria                                                          | Verified |
|----|-------------------------------------------------------------------|----------|
| 1  | Register creates company + HR user, returns tokens               | ☐        |
| 2  | Login validates bcrypt password, returns tokens                  | ☐        |
| 3  | Refresh issues new access token                                  | ☐        |
| 4  | Access token payload includes user_id, role, company_id          | ☐        |
| 5  | Expired tokens return 401                                        | ☐        |
| 6  | `require_role(HR)` blocks team_leader with 403                   | ☐        |
| 7  | Duplicate email returns 409                                      | ☐        |
| 8  | All T11.01–T11.06 tests pass                                    | ☐        |
