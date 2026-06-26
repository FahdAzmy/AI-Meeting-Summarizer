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
  platform: string;
  date: string;
  duration_minutes: number | null;
  participants: Array<string | { id: string; name: string; email: string; team_id?: string }>;
  transcript: string | null;
  summary: string | null;
  action_items: ActionItem[];
  decisions: string[];
  speaker_stats: SpeakerStatsObject | null;
  status: MeetingStatus;
  title?: string;
  error_message?: string;
}

export type UserRole = 'hr' | 'team_leader';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  company_id: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload extends LoginPayload {
  name: string;
  company_name: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  user: User;
}

export interface Team {
  id: string;
  name: string;
  leader_id: string | null;
  leader_email?: string | null;
  company_id: string;
  created_at?: string;
  members_count: number;
  members?: Member[];
}

export interface Member {
  id: string;
  name: string;
  email: string;
  team_id: string;
  company_id: string;
  created_at?: string;
}

export interface HRDashboardStats {
  total_teams: number;
  total_members: number;
  total_meetings: number;
  total_meeting_hours: number;
  most_active_team: string | null;
}

export interface TeamLeaderDashboardStats {
  team_members_count: number;
  meetings_this_month: number;
  pending_action_items: number;
}

export type DashboardStats = HRDashboardStats | TeamLeaderDashboardStats;

export interface CreateMeetingPayload {
  meeting_link: string;
  title?: string;
  team_ids: string[];
  member_ids: string[];

  storage?: string;
}

export interface PipelineStatus {
  session_id: string;
  status: MeetingStatus;
  step: number;
  total_steps: number;
  message: string;
}

export type StorageBackend = 'database';
export type STTProvider = 'whisper' | 'deepgram' | 'assemblyai';

export interface Settings {
  storage_backend: StorageBackend;
  stt_provider: STTProvider;
  email_sender: string;
  email_password?: string; // Optional for safety
}
