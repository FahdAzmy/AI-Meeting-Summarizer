import { Meeting, PipelineStatus, Settings } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const api = {
  async joinMeeting(meeting_link: string, emails: string[]): Promise<{ session_id: string }> {
    // MOCK IMPLEMENTATION
    return new Promise((resolve) => setTimeout(() => resolve({ session_id: 'mock_session_' + Date.now() }), 1000));
  },

  async getStatus(session_id: string): Promise<PipelineStatus> {
    // MOCK IMPLEMENTATION
    return new Promise((resolve) => setTimeout(() => resolve({
      session_id,
      status: 'summarising',
      step: 4,
      total_steps: 6,
      message: 'Generating the LLM analytical summary...'
    }), 500));
  },

  async getMeetings(): Promise<Partial<Meeting>[]> {
    // MOCK IMPLEMENTATION
    return new Promise((resolve) => setTimeout(() => resolve([
      {
        id: 'abc-1234',
        meeting_link: 'https://zoom.us/j/12345678',
        platform: 'zoom',
        date: '2026-03-14T15:00:00Z',
        duration_minutes: 45,
        summary: 'Discussed Q2 planning...',
        status: 'completed'
      }
    ]), 800));
  },

  async getMeeting(id: string): Promise<Meeting> {
    // MOCK IMPLEMENTATION
    return new Promise((resolve) => setTimeout(() => resolve({
      id,
      session_id: 'mock_session',
      meeting_link: 'https://zoom.us/j/12345678',
      platform: 'zoom',
      date: '2026-03-14T15:00:00Z',
      duration_minutes: 45,
      participants: ['dev@example.com'],
      transcript: 'Full literal text block here...',
      summary: 'Full formatted markdown summary here...',
      status: 'completed',
      action_items: [
        {
          assignee: 'Alice',
          task: 'Update backend docs',
          deadline: null
        }
      ],
      decisions: ['Adopt Next.js App Router'],
      speaker_stats: null
    }), 800));
  },

  async getSettings(): Promise<Settings> {
    // MOCK IMPLEMENTATION
    return new Promise((resolve) => setTimeout(() => resolve({
      storage_backend: 'database',
      stt_provider: 'whisper',
      email_sender: 'ai-assistant@company.com',
    }), 500));
  },

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    // MOCK IMPLEMENTATION
    return new Promise((resolve) => setTimeout(() => resolve({
      storage_backend: settings.storage_backend || 'database',
      stt_provider: settings.stt_provider || 'whisper',
      email_sender: settings.email_sender || 'ai-assistant@company.com',
    }), 800));
  }
};
