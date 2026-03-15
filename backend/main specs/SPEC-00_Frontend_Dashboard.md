# SPEC-00: Frontend Dashboard (Next.js)

| Field            | Details                                              |
|------------------|------------------------------------------------------|
| **Framework**    | Next.js 14+ (App Router, React 18, TypeScript)       |
| **Styling**      | Tailwind CSS or CSS Modules                          |
| **Backend API**  | Python FastAPI (async, separate service on port 8000)|
| **Traceability** | FR-D1 through FR-D11, NFR3, NFR13, NFR14            |
| **Version**      | 1.0                                                  |
| **Date**         | March 12, 2026                                       |

---

## 00.1 Architecture Overview

```
┌───────────────────────────────────────────┐       ┌──────────────────────────────────┐
│          NEXT.JS FRONTEND (:3000)         │       │  FASTAPI BACKEND API (:8000)      │
│                                           │       │                                  │
│  /              → Dashboard Page          │──────▶│  POST /api/join                  │
│  /history       → Meetings History Page   │──────▶│  GET  /api/meetings              │
│  /history/[id]  → Meeting Detail Page     │──────▶│  GET  /api/meetings/:id          │
│  /settings      → Settings Page           │──────▶│  GET  /api/settings              │
│                                           │──────▶│  POST /api/settings              │
│  /api/...       → Next.js API Routes      │──────▶│  GET  /api/status/:session_id    │
│  (optional proxy to Python backend)       │       │                                  │
└───────────────────────────────────────────┘       └──────────────────────────────────┘
```

The Next.js app serves the UI and communicates with the Python backend API via HTTP requests. The Python backend handles the meeting pipeline, database, and external integrations.

---

## 00.2 Project Structure

```
frontend/
├── package.json
├── next.config.js
├── tsconfig.json
├── tailwind.config.ts            # (if using Tailwind CSS)
│
├── public/
│   ├── favicon.ico
│   └── images/                   # Static assets
│
├── src/
│   ├── app/                      # App Router pages
│   │   ├── layout.tsx            # Root layout (navbar, sidebar, providers)
│   │   ├── page.tsx              # Dashboard Page — "/"
│   │   ├── history/
│   │   │   ├── page.tsx          # Meetings History Page — "/history"
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Meeting Detail Page — "/history/:id"
│   │   └── settings/
│   │       └── page.tsx          # Settings Page — "/settings"
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.tsx        # Top navigation bar
│   │   │   ├── Sidebar.tsx       # Side navigation links
│   │   │   └── Footer.tsx        # Footer
│   │   ├── dashboard/
│   │   │   ├── MeetingForm.tsx   # Meeting link + email input form
│   │   │   ├── PlatformBadge.tsx # Auto-detected platform badge
│   │   │   └── StatusPanel.tsx   # Live pipeline status display
│   │   ├── history/
│   │   │   ├── MeetingsTable.tsx # Sortable meetings history table
│   │   │   ├── MeetingRow.tsx    # Individual meeting row component
│   │   │   └── StatusBadge.tsx   # Colour-coded status badge
│   │   ├── detail/
│   │   │   ├── SummarySection.tsx    # Full meeting summary
│   │   │   ├── ActionItemsTable.tsx  # Action items table
│   │   │   ├── DecisionsList.tsx     # Decisions list
│   │   │   ├── TranscriptViewer.tsx  # Collapsible transcript
│   │   │   └── SpeakerStats.tsx      # Speaker participation chart
│   │   └── settings/
│   │       ├── StorageToggle.tsx     # DB vs Google Sheets radio group
│   │       ├── STTSelector.tsx       # STT provider dropdown
│   │       └── EmailConfig.tsx       # Email sender/password inputs
│   │
│   ├── lib/
│   │   ├── api.ts                # API client — fetch wrapper for backend
│   │   ├── types.ts              # TypeScript interfaces (Meeting, Settings, etc.)
│   │   └── utils.ts              # Helpers (platform detection, formatters)
│   │
│   └── styles/
│       └── globals.css           # Global styles
│
└── .env.local                    # NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 00.3 Pages & Routes

| Route              | File                              | Description                                          |
|--------------------|-----------------------------------|------------------------------------------------------|
| `/`                | `src/app/page.tsx`                | **Dashboard** — meeting link input + join button     |
| `/history`         | `src/app/history/page.tsx`        | **Meetings History** — sortable table of all meetings|
| `/history/[id]`    | `src/app/history/[id]/page.tsx`   | **Meeting Detail** — full summary & transcript       |
| `/settings`        | `src/app/settings/page.tsx`       | **Settings** — storage toggle, STT, email config     |

---

## 00.4 TypeScript Interfaces

```typescript
// src/lib/types.ts

export interface Meeting {
  _id: string;                      // MongoDB ObjectId as string
  session_id: string;
  meeting_link: string;
  platform: "google_meet" | "zoom" | "teams";
  date: string;                     // ISO 8601
  duration_minutes: number | null;
  participants: string[];           // array of emails
  transcript: string | null;
  summary: string | null;
  action_items: ActionItem[];       // embedded array
  decisions: string[];              // embedded array
  speaker_stats: SpeakerStats | null;
  status: MeetingStatus;
  audio_file_path: string | null;
  storage_backend: "database" | "google_sheets";
  failure_reason: string | null;
}

export type MeetingStatus =
  | "pending"
  | "joining"
  | "recording"
  | "transcribing"
  | "summarising"
  | "delivering"
  | "completed"
  | "failed";

export interface ActionItem {
  assignee: string;
  task: string;
  deadline: string | null;
}

export interface SpeakerStats {
  speakers: {
    speaker: string;
    total_speaking_time_sec: number;
    percentage_of_meeting: number;
    number_of_turns: number;
  }[];
  most_active_speaker: string;
  total_meeting_duration_sec: number;
}

export interface Settings {
  _id: string;                      // MongoDB ObjectId (singleton doc)
  storage_backend: "database" | "google_sheets";
  stt_provider: "whisper" | "deepgram" | "assemblyai";
  email_sender: string;
  email_password: string;
}

export interface PipelineStatus {
  session_id: string;
  status: MeetingStatus;
  step: number;
  total_steps: number;
  message: string;
}

export interface JoinMeetingRequest {
  meeting_link: string;
  emails: string[];
}
```

---

## 00.5 API Client

```typescript
// src/lib/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  // Dashboard
  joinMeeting: (data: JoinMeetingRequest) =>
    request<{ session_id: string }>("/api/join", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getStatus: (sessionId: string) =>
    request<PipelineStatus>(`/api/status/${sessionId}`),

  // History
  getMeetings: () =>
    request<Meeting[]>("/api/meetings"),

  getMeeting: (id: string) =>
    request<Meeting>(`/api/meetings/${id}`),

  // Settings
  getSettings: () =>
    request<Settings>("/api/settings"),

  updateSettings: (data: Partial<Settings>) =>
    request<Settings>("/api/settings", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
```

---

## 00.6 Page Specifications

### Dashboard Page — `src/app/page.tsx` **[M]**

| Component         | Description                                                        |
|-------------------|--------------------------------------------------------------------|
| `MeetingForm`     | URL input (`type="url"`, required), email textarea, submit button. |
| `PlatformBadge`   | Auto-detects platform from URL and shows icon/badge.               |
| `StatusPanel`     | Polls `/api/status/:session_id` every 3s while pipeline runs.      |

**User flow:**
1. User enters meeting link → `PlatformBadge` updates in real time.
2. User enters comma-separated participant emails.
3. User clicks **"🚀 Join Meeting"** → `api.joinMeeting()` called.
4. `StatusPanel` appears, polling `/api/status/:session_id`.
5. On status `"completed"` → show success toast + link to history.

**Client-side validation:**

| Rule                     | Implementation                                              |
|--------------------------|-------------------------------------------------------------|
| URL format               | HTML5 `type="url"` + regex check for supported platforms    |
| Platform detection       | Regex: `/meet\.google\.com|zoom\.us|teams\.microsoft\.com/` |
| Emails non-empty         | Check textarea is not empty, split by commas, trim          |
| Email format per entry   | Basic email regex validation on each entry **[S]**          |

---

### Meetings History Page — `src/app/history/page.tsx` **[M]**

| Component         | Description                                                        |
|-------------------|--------------------------------------------------------------------|
| `MeetingsTable`   | Fetches `api.getMeetings()` on mount. Sortable columns.            |
| `MeetingRow`      | Renders one meeting row with date, platform badge, summary preview.|
| `StatusBadge`     | Colour-coded: green=completed, yellow=processing, red=failed.     |

**Table columns:**

| Column           | Data Source               | Sortable |
|------------------|---------------------------|----------|
| Date             | `meeting.date`            | ✅       |
| Platform         | `meeting.platform`        | ✅       |
| Duration         | `meeting.duration_minutes` | ✅       |
| Summary Preview  | `meeting.summary` (first 100 chars) | ❌ |
| Status           | `meeting.status`          | ✅       |
| Action           | Link → `/history/:id`    | ❌       |

**Performance:** Table must render within 2 seconds for 100+ records (NFR13). Use client-side sorting (no full re-fetch).

---

### Meeting Detail Page — `src/app/history/[id]/page.tsx` **[M]**

| Component            | Description                                                    |
|----------------------|----------------------------------------------------------------|
| `SummarySection`     | Renders the full markdown summary.                             |
| `ActionItemsTable`   | Table: Assignee → Task → Deadline.                             |
| `DecisionsList`      | Numbered list of decisions.                                    |
| `TranscriptViewer`   | Collapsible full transcript with expand/collapse toggle.       |
| `SpeakerStats`       | Bar chart or stats cards (if diarisation data available).      |

**Sections displayed:**
1. **Meeting Overview** — date, platform, duration, original link
2. **Summary** — full LLM-generated summary (rendered as markdown)
3. **Action Items** — parsed from `meeting.action_items` JSON
4. **Decisions** — parsed from `meeting.decisions` JSON
5. **Transcript** — collapsible, scrollable viewer
6. **Speaker Statistics** — rendered only if `speaker_stats` is not null

**404 handling:** Show a "Meeting not found" page when `api.getMeeting(id)` returns 404.

---

### Settings Page — `src/app/settings/page.tsx` **[M]**

| Component         | Description                                                        |
|-------------------|--------------------------------------------------------------------|
| `StorageToggle`   | Radio group: "Database (MongoDB)" vs "Google Sheets".              |
| `STTSelector`     | Dropdown: Whisper API, Deepgram, AssemblyAI.                       |
| `EmailConfig`     | Sender email input + app password input (masked).                  |

**Behaviour:**
1. On mount → `api.getSettings()` → populate form with current values.
2. On submit → `api.updateSettings(formData)` → show success toast.
3. Effect is **immediate** for all subsequent meetings (NFR14).

**Allowed values:**

| Field              | Valid Values                               |
|--------------------|--------------------------------------------|
| `storage_backend`  | `"database"`, `"google_sheets"`            |
| `stt_provider`     | `"whisper"`, `"deepgram"`, `"assemblyai"`  |

---

## 00.7 Backend API Endpoints (Python)

The Next.js frontend calls these endpoints on the Python backend:

| Endpoint                    | Method | Request Body                               | Response                         |
|-----------------------------|--------|--------------------------------------------|----------------------------------|
| `/api/join`                 | POST   | `{ meeting_link: str, emails: str[] }`     | `{ session_id: str }`            |
| `/api/status/<session_id>`  | GET    | —                                          | `PipelineStatus` JSON            |
| `/api/meetings`             | GET    | —                                          | `Meeting[]` JSON                 |
| `/api/meetings/<id>`        | GET    | —                                          | `Meeting` JSON (or 404)          |
| `/api/settings`             | GET    | —                                          | `Settings` JSON                  |
| `/api/settings`             | POST   | `Partial<Settings>` JSON body              | `Settings` JSON (updated)        |

> **CORS:** The Python backend must enable CORS for `http://localhost:3000` (the Next.js dev server) using FastAPI's `CORSMiddleware`.

---

## 00.8 Root Layout — `src/app/layout.tsx`

```tsx
// Provides global navigation and consistent page structure
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <div className="app-container">
          <Sidebar />
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
```

**Navbar links:**

| Label            | Route        | Icon  |
|------------------|--------------|-------|
| Dashboard        | `/`          | 🏠    |
| Meeting History  | `/history`   | 📋    |
| Settings         | `/settings`  | ⚙️    |

---

## 00.9 Environment Variables

```env
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 00.10 Acceptance Criteria

| #  | Criteria                                                             | Verified |
|----|----------------------------------------------------------------------|----------|
| 1  | `npm run dev` starts Next.js on port 3000 without errors.           | ☐        |
| 2  | Dashboard page renders with meeting link input and Join button.      | ☐        |
| 3  | Platform badge detects Google Meet, Zoom, and Teams URLs.            | ☐        |
| 4  | `/join` API call triggers the pipeline and returns session_id.       | ☐        |
| 5  | StatusPanel polls and displays live pipeline progress.               | ☐        |
| 6  | History page lists meetings sorted by date descending.               | ☐        |
| 7  | Meeting detail page shows summary, transcript, and action items.     | ☐        |
| 8  | Settings page loads current settings and saves changes immediately.  | ☐        |
| 9  | Storage backend toggle persists and takes effect for next meeting.   | ☐        |
| 10 | All pages are responsive and render correctly on mobile + desktop.   | ☐        |
