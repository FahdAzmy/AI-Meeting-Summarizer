export type Platform = 'google_meet' | 'zoom' | 'teams';

export type MeetingStatus = 'pending' | 'joining' | 'recording' | 'transcribing' | 'summarising' | 'delivering' | 'completed' | 'failed';

export interface ActionItem {
  assignee: string;
  task: string;
  deadline: string | null;
}

export interface SpeakerStatsObject {
  [speaker: string]: {
    duration: number;
    percentage: number;
  };
}

export interface Meeting {
  id: string;
  session_id: string;
  meeting_link: string;
  platform: Platform;
  date: string;
  duration_minutes: number | null;
  participants: string[];
  transcript: string | null;
  summary: string | null;
  action_items: ActionItem[];
  decisions: string[];
  speaker_stats: SpeakerStatsObject | null;
  status: MeetingStatus;
}

export interface PipelineStatus {
  session_id: string;
  status: MeetingStatus;
  step: number;
  total_steps: number;
  message: string;
}

export type StorageBackend = 'database' | 'google_sheets';
export type STTProvider = 'whisper' | 'deepgram' | 'assemblyai';

export interface Settings {
  storage_backend: StorageBackend;
  stt_provider: STTProvider;
  email_sender: string;
  email_password?: string; // Optional for safety
}
