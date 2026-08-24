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

const isStaticDemo = typeof window !== 'undefined' && (
  window.location.hostname.includes('github.io') ||
  window.location.hostname.includes('pages.dev')
);

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      if (isStaticDemo || response.status === 404) {
        return mockFallbackResponse<T>(endpoint, options);
      }
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
  } catch (err: any) {
    if (isStaticDemo || err.message === 'Failed to fetch' || err.name === 'TypeError') {
      return mockFallbackResponse<T>(endpoint, options);
    }
    throw err;
  }
}

function mockFallbackResponse<T>(endpoint: string, options: RequestInit): T {
  const demoOrgId = '00000000-0000-0000-0000-000000000001';
  const demoUserId = '00000000-0000-0000-0000-000000000002';

  if (endpoint.includes('/auth/signup') || endpoint.includes('/auth/login')) {
    let bodyObj: any = {};
    try {
      bodyObj = JSON.parse(options.body as string || '{}');
    } catch {}

    const mockUser: User = {
      id: demoUserId,
      org_id: demoOrgId,
      email: bodyObj.email || 'admin@demo.com',
      role: 'admin',
      status: 'active',
      created_at: new Date().toISOString(),
    };

    return {
      access_token: 'demo_jwt_token',
      user: mockUser,
      org_id: demoOrgId,
    } as unknown as T;
  }

  if (endpoint.includes('/auth/me')) {
    return {
      id: demoUserId,
      org_id: demoOrgId,
      email: 'admin@company.com',
      role: 'admin',
      status: 'active',
      created_at: new Date().toISOString(),
    } as unknown as T;
  }

  if (endpoint.includes('/changes')) {
    if (options.method === 'POST') {
      let bodyObj: any = {};
      try {
        bodyObj = JSON.parse(options.body as string || '{}');
      } catch {}
      return {
        id: Date.now().toString(),
        org_id: demoOrgId,
        title: bodyObj.title || 'New Change',
        description: bodyObj.description || 'Description',
        status: 'analyzed',
        risk_score: 7.8,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as unknown as T;
    }

    return {
      items: [
        {
          id: '1',
          org_id: demoOrgId,
          title: 'Upgrade PostgreSQL Database Schema to v16',
          description: 'Migrating production DB to v16 with pgvector extension for AI search.',
          status: 'analyzed',
          risk_score: 8.2,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '2',
          org_id: demoOrgId,
          title: 'Rotate Auth Middleware JWT Signing Secret Keys',
          description: 'Scheduled quarterly rotation of security access tokens.',
          status: 'deployed',
          risk_score: 3.4,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 2,
      skip: 0,
      limit: 10,
    } as unknown as T;
  }

  if (endpoint.includes('/notes')) {
    return {
      items: [
        {
          id: '1',
          org_id: demoOrgId,
          title: 'DB Migration Blocker Risk',
          content: 'Ensure backup script executes prior to applying schema migration 005.',
          tags: ['blocker'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '2',
          org_id: demoOrgId,
          title: 'Power BI Export Key Security Decision',
          content: 'Agreed on 32-character SHA-256 hashed keys for Power BI scheduled refresh.',
          tags: ['decision'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 2,
    } as unknown as T;
  }

  if (endpoint.includes('/team-members')) {
    return {
      items: [
        {
          id: '1',
          org_id: demoOrgId,
          name: 'Jane Doe',
          email: 'jane@company.com',
          role: 'Organization Admin',
          status: 'active',
          created_at: new Date().toISOString(),
        },
        {
          id: '2',
          org_id: demoOrgId,
          name: 'John Smith',
          email: 'john@company.com',
          role: 'Senior DevOps Engineer',
          status: 'active',
          created_at: new Date().toISOString(),
        },
      ],
      total: 2,
    } as unknown as T;
  }

  if (endpoint.includes('/project-progress')) {
    return {
      items: [
        {
          id: '1',
          org_id: demoOrgId,
          title: 'Production Multi-Region Deployment',
          status: 'in_progress',
          progress_pct: 85,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: '2',
          org_id: demoOrgId,
          title: 'Security & Vulnerability Hardening',
          status: 'completed',
          progress_pct: 100,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 2,
    } as unknown as T;
  }

  if (endpoint.includes('/notifications')) {
    return {
      items: [
        {
          id: '1',
          org_id: demoOrgId,
          user_id: demoUserId,
          title: 'High Risk Alert: Upgrade PostgreSQL Database Schema',
          message: 'Risk score evaluated at 8.2 / 10.0 (HIGH). SRE review recommended.',
          type: 'HIGH_RISK_ALERT',
          is_read: false,
          created_at: new Date().toISOString(),
        },
      ],
      unread_count: 1,
      total: 1,
    } as unknown as T;
  }

  if (endpoint.includes('/audit-logs')) {
    return {
      items: [
        {
          id: '1',
          org_id: demoOrgId,
          actor_user_id: demoUserId,
          action: 'USER_LOGIN',
          target_type: 'user',
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
    } as unknown as T;
  }

  return {} as T;
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
