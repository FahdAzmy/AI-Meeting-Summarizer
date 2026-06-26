import {
  CreateMeetingPayload,
  DashboardStats,
  LoginPayload,
  Member,
  Meeting,
  PipelineStatus,
  RegisterPayload,
  Settings,
  Team,
  TokenResponse,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const ACCESS_TOKEN_KEY = 'meetingai_access_token';
const REFRESH_TOKEN_KEY = 'meetingai_refresh_token';
const USER_KEY = 'meetingai_user';

// ── Auth failure callback (registered by AuthProvider) ──────────────────────
let _onAuthFailure: (() => void) | null = null;

/**
 * Register a callback that fires when tokens are unrecoverable (refresh
 * token expired or invalid). The AuthProvider uses this to trigger logout.
 */
export function registerAuthFailureCallback(cb: () => void) {
  _onAuthFailure = cb;
}

export function unregisterAuthFailureCallback() {
  _onAuthFailure = null;
}

// ── Token refresh with concurrency lock ─────────────────────────────────────
let _refreshPromise: Promise<string> | null = null;

/**
 * Attempt to get a new access token using the stored refresh token.
 * If multiple callers invoke this concurrently, only ONE network request
 * is made — the rest share the same Promise.
 */
async function refreshAccessToken(): Promise<string> {
  // If a refresh is already in-flight, piggyback on it
  if (_refreshPromise) return _refreshPromise;

  _refreshPromise = (async () => {
    const refreshToken = window.localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      // Refresh token itself is invalid/expired — unrecoverable
      throw new Error('Refresh token expired');
    }

    const data: TokenResponse = await res.json();

    // Persist the new tokens
    window.localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
    window.localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
    window.localStorage.setItem(USER_KEY, JSON.stringify(data.user));

    return data.access_token;
  })();

  try {
    return await _refreshPromise;
  } finally {
    _refreshPromise = null;
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const token = window.localStorage.getItem(ACCESS_TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function buildHeaders(init: RequestInit): Record<string, string> {
  const extra: Record<string, string> = {};
  if (init.headers) {
    const h = init.headers;
    if (h instanceof Headers) {
      h.forEach((v, k) => { extra[k] = v; });
    } else if (Array.isArray(h)) {
      h.forEach(([k, v]) => { extra[k] = v; });
    } else {
      Object.assign(extra, h);
    }
  }
  return {
    ...(init.body ? { 'Content-Type': 'application/json' } : {}),
    ...authHeaders(),
    ...extra,
  };
}

/**
 * Core request function with automatic 401 → refresh → retry.
 * The `_isRetry` flag prevents infinite loops.
 */
async function request<T>(
  path: string,
  init: RequestInit = {},
  _isRetry = false,
): Promise<T> {
  const headers = buildHeaders(init);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  // ── Handle 401: attempt silent refresh then retry once ──
  const isAuthRoute = path.startsWith('/auth/login') || path.startsWith('/auth/register');
  if (res.status === 401 && !_isRetry && typeof window !== 'undefined' && !isAuthRoute) {
    try {
      const newToken = await refreshAccessToken();
      // Retry with the fresh token
      const retryHeaders = {
        ...headers,
        Authorization: `Bearer ${newToken}`,
      };
      return request<T>(path, { ...init, headers: retryHeaders }, true);
    } catch {
      // Refresh failed — trigger logout
      _onAuthFailure?.();
      throw new Error('Session expired. Please log in again.');
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    const detail = typeof err.detail === 'string' ? err.detail : err.detail?.message;
    throw new Error(detail || 'Request failed');
  }
  return res.json();
}

/**
 * Download helper with automatic 401 → refresh → retry.
 */
async function download(
  path: string,
  fallbackName: string,
  _isRetry = false,
): Promise<void> {
  const headers = authHeaders();
  const res = await fetch(`${API_BASE}${path}`, { headers });

  // ── Handle 401: attempt silent refresh then retry once ──
  if (res.status === 401 && !_isRetry && typeof window !== 'undefined') {
    try {
      await refreshAccessToken();
      return download(path, fallbackName, true);
    } catch {
      _onAuthFailure?.();
      throw new Error('Session expired. Please log in again.');
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Export failed' }));
    throw new Error(err.detail || 'Failed to export');
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = res.headers.get('content-disposition')?.match(/filename="(.+)"/)?.[1] || fallbackName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export const api = {
  login(payload: LoginPayload): Promise<TokenResponse> {
    return request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  register(payload: RegisterPayload): Promise<TokenResponse> {
    return request<TokenResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getMe(): Promise<TokenResponse['user']> {
    return request<TokenResponse['user']>('/auth/me');
  },

  async joinMeeting(payload: CreateMeetingPayload): Promise<{ session_id: string }> {
    return request<{ session_id: string }>('/trigger', {
      method: 'POST',
      body: JSON.stringify({ ...payload, storage: payload.storage ?? 'email' }),
    });
  },

  getStatus(session_id: string): Promise<PipelineStatus> {
    return request<PipelineStatus>(`/status/${session_id}`);
  },

  getDashboard(): Promise<DashboardStats> {
    return request<DashboardStats>('/dashboard');
  },

  getTeams(): Promise<Team[]> {
    return request<Team[]>('/teams');
  },

  getTeam(id: string): Promise<Team> {
    return request<Team>(`/teams/${id}`);
  },

  createTeam(name: string): Promise<Team> {
    return request<Team>('/teams', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  },

  updateTeam(id: string, name: string): Promise<Team> {
    return request<Team>(`/teams/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ name }),
    });
  },

  assignLeader(teamId: string, userId: string): Promise<Team> {
    return request<Team>(`/teams/${teamId}/leader`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  },

  deleteTeam(id: string): Promise<{ message: string }> {
    return request<{ message: string }>(`/teams/${id}`, { method: 'DELETE' });
  },

  getMembers(teamId?: string): Promise<Member[]> {
    return request<Member[]>(teamId ? `/members?team_id=${teamId}` : '/members');
  },

  createMember(payload: Pick<Member, 'name' | 'email' | 'team_id'>): Promise<Member> {
    return request<Member>('/members', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  updateMember(id: string, payload: Partial<Pick<Member, 'name' | 'email'>>): Promise<Member> {
    return request<Member>(`/members/${id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  deleteMember(id: string): Promise<{ message: string }> {
    return request<{ message: string }>(`/members/${id}`, { method: 'DELETE' });
  },

  getMeetings(): Promise<Partial<Meeting>[]> {
    return request<Partial<Meeting>[]>('/meetings');
  },

  getMeeting(id: string): Promise<Meeting> {
    return request<Meeting>(`/meetings/${id}`);
  },

  getSettings(): Promise<Settings> {
    return request<Settings>('/settings');
  },

  updateSettings(settings: Partial<Settings>): Promise<Settings> {
    return request<Settings>('/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  },

  exportAllMeetingsExcel(): Promise<void> {
    return download('/export/meetings/excel', 'meetings.xlsx');
  },

  exportMeetingExcel(id: string): Promise<void> {
    return download(`/export/meetings/${id}/excel`, 'meeting.xlsx');
  },

  exportMeetingPdf(id: string): Promise<void> {
    return download(`/export/meetings/${id}/pdf`, 'meeting.pdf');
  },
};
