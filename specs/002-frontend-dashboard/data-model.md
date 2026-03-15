# Data Model: Frontend Dashboard

This file defines the primary abstract data structures consumed and managed by the Next.js frontend application. These maps directly to TypeScript interfaces inside `frontend/src/lib/types.ts`.

## 1. Meeting

Represents the core record of an AI Meeting.

- **id** (String) - Global persistent meeting identifier.
- **session_id** (String) - Identifier tying the pipeline process run.
- **meeting_link** (String) 
- **platform** (Enum: `google_meet` | `zoom` | `teams`)
- **date** (DateTime string - ISO 8601)
- **duration_minutes** (Integer | nullable)
- **participants** (Array of Strings / Emails)
- **transcript** (String | nullable)
- **summary** (String | nullable)
- **action_items** (Array of ActionItems)
- **decisions** (Array of Strings)
- **speaker_stats** (SpeakerStatsObject | nullable)
- **status** (Enum: `pending` | `joining` | `recording` | `transcribing` | `summarising` | `delivering` | `completed` | `failed`)

## 2. ActionItem

Micro-entity embedded in Meeting.

- **assignee** (String)
- **task** (String)
- **deadline** (String | nullable)

## 3. Settings

Singleton document fetched for global config management.

- **storage_backend** (Enum: `database` | `google_sheets`)
- **stt_provider** (Enum: `whisper` | `deepgram` | `assemblyai`)
- **email_sender** (String)
- **email_password** (String)

## 4. PipelineStatus

Lightweight object fetched during polling to see current live progress.

- **session_id** (String)
- **status** (MeetingStatus Enum above)
- **step** (Integer) - E.g., step 4
- **total_steps** (Integer) - E.g., 6 total steps
- **message** (String) - Human readable label (e.g. "Transcribing audio...")
