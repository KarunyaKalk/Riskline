import {
  AuditLog,
  Change,
  ChatMessage,
  Note,
  Notification,
  NotificationPreference,
  OrgInvite,
  ProjectProgress,
  RiskAnalysis,
  TeamMember,
  User,
  UserRole,
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  // Auth
  signup: (payload: { org_name: string; email: string; password: string; name?: string }) =>
    request<{ access_token: string; user: User; org_id: string }>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  login: (payload: { email: string; password: string }) =>
    request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  logout: () => request<{ message: string }>('/auth/logout', { method: 'POST' }),

  me: () => request<User>('/auth/me'),

  // Changes
  listChanges: (statusFilter?: string) => {
    const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : '';
    return request<{ items: Change[]; total: number; skip: number; limit: number }>(`/changes${query}`);
  },

  getChange: (id: string) => request<Change>(`/changes/${id}`),

  createChange: (payload: { title: string; description: string; status?: string }) =>
    request<Change>('/changes', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  uploadPdfChange: (file: File, title?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    return request<Change>('/changes/upload-pdf', {
      method: 'POST',
      body: formData,
    });
  },

  triggerAnalysis: (id: string) => request<RiskAnalysis>(`/changes/${id}/analyze`, { method: 'POST' }),

  getRiskAnalysis: (id: string) => request<RiskAnalysis>(`/changes/${id}/risk-analysis`),

  // Notes
  listNotes: (tag?: string) => {
    const query = tag && tag !== 'all' ? `?tag=${encodeURIComponent(tag)}` : '';
    return request<{ items: Note[]; total: number }>(`/notes${query}`);
  },

  createNote: (payload: { title: string; content: string; tags?: string[] }) =>
    request<Note>('/notes', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  deleteNote: (id: string) => request<void>(`/notes/${id}`, { method: 'DELETE' }),

  // Team Roster
  listRoster: () => request<{ items: TeamMember[]; total: number }>('/team-members'),

  createRosterMember: (payload: { name: string; email: string; role: string }) =>
    request<TeamMember>('/team-members', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Project Progress
  listProgress: () => request<{ items: ProjectProgress[]; total: number }>('/project-progress'),

  createProgress: (payload: { title: string; progress_pct: number; status: string }) =>
    request<ProjectProgress>('/project-progress', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Org Settings & Invites
  createInvite: (payload: { email: string; role: UserRole }) =>
    request<OrgInvite>('/orgs/invites', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  acceptInvite: (payload: { token: string; password: string; name?: string }) =>
    request<{ access_token: string; user: User }>('/orgs/invites/accept', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  updateMemberRole: (userId: string, role: UserRole) =>
    request<User>(`/orgs/members/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    }),

  removeMember: (userId: string) => request<void>(`/orgs/members/${userId}`, { method: 'DELETE' }),

  // Notifications
  listNotifications: () =>
    request<{ items: Notification[]; unread_count: number; total: number }>('/notifications'),

  markNotificationRead: (id: string) =>
    request<Notification>(`/notifications/${id}/read`, { method: 'PUT' }),

  getNotificationPreferences: () => request<NotificationPreference>('/notifications/preferences'),

  updateNotificationPreferences: (payload: Partial<NotificationPreference>) =>
    request<NotificationPreference>('/notifications/preferences', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  // Audit Logs
  listAuditLogs: (actionFilter?: string) => {
    const query = actionFilter ? `?action_filter=${encodeURIComponent(actionFilter)}` : '';
    return request<{ items: AuditLog[]; total: number }>(`/audit-logs${query}`);
  },

  // Chat History
  getChatHistory: (sessionId: string = 'main') =>
    request<{ items: ChatMessage[]; total: number }>(`/chat/history?session_id=${encodeURIComponent(sessionId)}`),
};
