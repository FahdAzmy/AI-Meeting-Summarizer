# Data Model: Meeting Export (Excel & PDF)

**Branch**: `010-meeting-export` | **Date**: 2026-04-26

## Existing Entities (No Schema Changes)

This feature does **not** modify the database schema. It reads from the existing `Meeting` collection and generates export files on-demand.

### Meeting (MongoDB — `meetings` collection)

The existing Beanie document is the sole data source for all exports.

| Field | Type | Required | Export Usage |
|-------|------|----------|--------------|
| `id` | `PydanticObjectId` | Auto | Internal reference only |
| `title` | `Optional[str]` | No | Display title (with fallback) |
| `meeting_link` | `Optional[str]` | No | Not exported directly |
| `session_id` | `Optional[str]` | No | Not exported |
| `platform` | `Optional[str]` | No | Used in fallback title generation |
| `created_at` | `datetime` | Yes (auto) | "Date" column in Excel, header in PDF |
| `status` | `MeetingStatus` (enum) | Yes | Filter: only `COMPLETED` meetings exported |
| `duration_minutes` | `Optional[int]` | No | "Duration" column/section |
| `transcript` | `Optional[str]` | No | Full transcript section in PDF, column in Excel |
| `summary` | `Optional[str]` | No | Summary section/column |
| `action_items` | `list[dict]` | Yes (default `[]`) | Action items section/column |
| `decisions` | `list[str]` | Yes (default `[]`) | Decisions section/column |
| `follow_up` | `list[str]` | Yes (default `[]`) | Follow-up section/column |
| `speaker_stats` | `Optional[dict]` | No | Participants extracted from speakers list |

### Derived: Display Title (computed, not stored)

When `title` is `None` or empty, the export endpoints compute a display title:

```
Format: "{platform} — {created_at formatted as 'Mon DD, YYYY'}"
Example: "Google Meet — Apr 26, 2026"
Fallback: "Meeting — Apr 26, 2026" (when platform is also null)
```

### Derived: Participants List (computed from speaker_stats)

Participants are extracted from `speaker_stats.speakers[].speaker` names. When `speaker_stats` is `None`, the participants field shows "N/A".

## Export File Structures

### Excel — All Meetings (one row per meeting)

| Column | Source Field | Format |
|--------|-------------|--------|
| Title | `title` (or computed fallback) | Plain text |
| Date | `created_at` | `YYYY-MM-DD` |
| Duration (min) | `duration_minutes` | Integer |
| Participants | `speaker_stats.speakers` | Comma-separated names |
| Summary | `summary` | Plain text |
| Decisions | `decisions` | Newline-separated list |
| Action Items | `action_items` | `"Assignee: Task (Deadline)"` per line |
| Follow-up | `follow_up` | Newline-separated list |

### Excel — Single Meeting

Same columns as above, but a single row. May include additional formatting or multiple sheets for readability.

### PDF — Single Meeting

Structured document with these sections (in order):

1. **Header**: Title, date, duration, platform
2. **Participants**: List of attendees from speaker_stats
3. **Summary**: Full AI-generated summary text
4. **Key Decisions**: Bulleted list
5. **Action Items**: Table with Assignee | Task | Deadline columns
6. **Follow-up Items**: Bulleted list
7. **Transcript**: Full transcript text (omitted if null)

Sections with no data are omitted entirely (FR-012).

## State Transitions

No new state transitions. The export feature is read-only and only queries meetings where `status == MeetingStatus.COMPLETED` (FR-010).
