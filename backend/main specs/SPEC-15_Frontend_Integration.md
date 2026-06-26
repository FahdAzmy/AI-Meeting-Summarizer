# SPEC-15: Frontend Integration

| Field            | Details                                                    |
|------------------|------------------------------------------------------------|
| **Scope**        | Frontend Authentication, Dashboard UI, Teams & Members CRUD, Meeting Form Updates |
| **Files**        | `frontend/src/app/login/page.tsx`, `frontend/src/app/register/page.tsx`, `frontend/src/lib/auth.ts`, `frontend/src/lib/api.ts`, `frontend/src/app/dashboard/page.tsx`, `frontend/src/app/teams/page.tsx`, `frontend/src/app/teams/[id]/page.tsx`, `frontend/src/components/dashboard/MeetingForm.tsx`, `frontend/src/components/ui/Sidebar.tsx` |
| **Traceability** | Phase 8 — Frontend Integration                             |
| **Framework**    | Next.js App Router (React) + Tailwind/CSS modules         |
| **Depends On**   | SPEC-11 (Auth API), SPEC-12 (Teams/Members API), SPEC-13 (Trigger Update), SPEC-14 (Dashboard API) |
| **Version**      | 1.0                                                        |
| **Date**         | June 17, 2026                                              |

---

## 15.1 Objective

Update the Next.js frontend to support:
1. **User Authentication**: Sign-up (Register) and Log-in interfaces with token persistence.
2. **Dashboard UI**: Role-specific metric cards and summaries (HR vs. Team Leader).
3. **Teams & Members Management**: Admin pages to manage team hierarchies, team leader assignments, and members.
4. **Interactive Meeting Creation**: Update the meeting creation form to allow scheduling meetings and selecting team/member participants via dropdowns instead of raw emails.

---

## 15.2 Test Plan (TDD - Frontend E2E / Component Tests)

### T15.01 — Auth State & Protected Layout

```typescript
// frontend/__tests__/auth.test.tsx
import { render, screen } from '@testing-library/react';
import { AuthProvider, useAuth } from '../src/lib/auth';

const DummyChild = () => {
  const { user, isAuthenticated } = useAuth();
  return (
    <div>
      <span data-testid="auth-status">{isAuthenticated ? "logged-in" : "guest"}</span>
      {user && <span data-testid="user-role">{user.role}</span>}
    </div>
  );
};

test('provides unauthenticated state by default', () => {
  render(
    <AuthProvider>
      <DummyChild />
    </AuthProvider>
  );
  expect(screen.getByTestId('auth-status')).toHaveTextContent('guest');
});
```

### T15.02 — Login & Redirects

```typescript
// frontend/__tests__/login.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from '../src/app/login/page';
import { act } from 'react-dom/test-utils';

test('submitting login form with credentials calls login API', async () => {
  const mockLogin = jest.fn();
  render(<LoginPage onSubmit={mockLogin} />);
  
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'hr@company.com' } });
  fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
  
  act(() => {
    fireEvent.click(screen.getByRole('button', { name: /log in/i }));
  });

  await waitFor(() => {
    expect(mockLogin).toHaveBeenCalledWith('hr@company.com', 'password123');
  });
});
```

### T15.03 — Team Management & Member Creation (HR View)

```typescript
// frontend/__tests__/teams.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import TeamsPage from '../src/app/teams/page';

test('renders teams list and create team button for HR user', () => {
  const mockTeams = [{ id: '1', name: 'Dev Team', leader_id: null, members_count: 5 }];
  render(<TeamsPage initialTeams={mockTeams} userRole="hr" />);
  
  expect(screen.getByText('Dev Team')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /create team/i })).toBeInTheDocument();
});

test('hides create team button for Team Leader user', () => {
  const mockTeams = [{ id: '1', name: 'Dev Team', leader_id: 'tl_123', members_count: 5 }];
  render(<TeamsPage initialTeams={mockTeams} userRole="team_leader" />);
  
  expect(screen.queryByRole('button', { name: /create team/i })).not.toBeInTheDocument();
});
```

---

## 15.3 Authentication Provider & Storage

```typescript
// frontend/src/lib/auth.ts
"use client";
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'hr' | 'team_leader';
  company_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: any) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}
```

- **Persistence**: Access token and refresh token saved in `localStorage` or secured cookies.
- **Request Interceptor**: Axios/Fetch client is updated to add the `Authorization: Bearer <token>` header on all requests to `/api`.

---

## 15.4 UI Views

### 15.4.1 Dashboard Layout
- **HR Dashboard**: Shows four bento-style metric cards:
  - *Total Teams*
  - *Total Members*
  - *Total Meetings*
  - *Total Meeting Hours*
  - List of overall active teams and summary details.
- **Team Leader Dashboard**: Scopes metrics:
  - *Team Members Count*
  - *Meetings this Month*
  - *Pending Action Items*

### 15.4.2 Teams Page
- A list of teams scoped by the tenant.
- HR users see a "Create New Team" modal and can assign users with the `team_leader` role to a team.
- Clicking a team card navigates to `/teams/[id]`.

### 15.4.3 Team Details & Members CRUD
- View team detail, current team leader, and the members list.
- HR and assigned Team Leaders can:
  - Add a member to the team (modal asking for `name` and `email`).
  - Edit member information.
  - Delete a member (removes them from the team and company scope).

---

## 15.5 MeetingForm Refactoring

The meeting creation form is updated to handle team-based selection:
- Queries `/api/teams` and `/api/members` to list selectable options.
- Displays select elements allowing multi-select for entire teams or specific individual members.
- Adds an optional `scheduled_time` datetime input field to support scheduled reminder notifications.

```typescript
// src/components/dashboard/MeetingForm.tsx
interface CreateMeetingPayload {
  meeting_link: string;
  title?: string;
  team_ids: string[];
  member_ids: string[];
  scheduled_time?: string;
}
```

---

## 15.6 Acceptance Criteria

| #  | Criteria                                                              | Verified |
|----|-----------------------------------------------------------------------|----------|
| 1  | Unauthenticated users are redirected to `/login`                      | ☐        |
| 2  | Auth tokens persist across page updates and refreshes                 | ☐        |
| 3  | HR users view full team CRUD and leader assignment interface          | ☐        |
| 4  | Team Leaders can only view their own team and manage its members      | ☐        |
| 5  | Dashboard shows different UI layouts depending on user role           | ☐        |
| 6  | Meeting form supports multi-selecting teams and individual members    | ☐        |
| 7  | Form sends valid JSON containing `team_ids` and `member_ids`          | ☐        |
| 8  | Sidebar adjusts available routes/actions dynamically based on user role | ☐        |
| 9  | All T15.01-T15.03 frontend tests pass                                | ☐        |
