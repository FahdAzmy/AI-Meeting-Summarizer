import { Meeting, PipelineStatus, Settings } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const api = {
  async joinMeeting(meeting_link: string, emails: string[]): Promise<{ session_id: string }> {
    const res = await fetch(`${API_BASE}/trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meeting_link, emails, storage: 'email' }),
    });
    if (!res.ok) throw new Error('Failed to trigger meeting pipeline');
    return res.json();
  },

  async getStatus(session_id: string): Promise<PipelineStatus> {
    const res = await fetch(`${API_BASE}/status/${session_id}`);
    if (!res.ok) throw new Error('Failed to fetch status');
    return res.json();
  },

  async getMeetings(): Promise<Partial<Meeting>[]> {
    const res = await fetch(`${API_BASE}/meetings`);
    if (!res.ok) throw new Error('Failed to fetch meetings');
    return res.json();
  },

  async getMeeting(id: string): Promise<Meeting> {
    const res = await fetch(`${API_BASE}/meetings/${id}`);
    if (!res.ok) throw new Error('Failed to fetch meeting details');
    return res.json();
  },

  async getSettings(): Promise<Settings> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  }
};
