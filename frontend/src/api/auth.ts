import { AuthResponse, LoginPayload, SignupPayload, User, UserMeResponse } from '../types';

const API_BASE = '/api/v1/auth';

const getHeaders = (token?: string | null): HeadersInit => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const storedToken = token || localStorage.getItem('access_token');
  if (storedToken) {
    headers['Authorization'] = `Bearer ${storedToken}`;
  }
  return headers;
};

export const authApi = {
  async signup(payload: SignupPayload): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/signup`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
      credentials: 'include',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Signup failed' }));
      throw new Error(err.detail || 'Signup failed');
    }
    const data: AuthResponse = await res.json();
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
    }
    return data;
  },

  async login(payload: LoginPayload): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(payload),
      credentials: 'include',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Incorrect email or password');
    }
    const data: AuthResponse = await res.json();
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
    }
    return data;
  },

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE}/logout`, {
        method: 'POST',
        headers: getHeaders(),
        credentials: 'include',
      });
    } finally {
      localStorage.removeItem('access_token');
    }
  },

  async getMe(): Promise<UserMeResponse> {
    const res = await fetch(`${API_BASE}/me`, {
      method: 'GET',
      headers: getHeaders(),
      credentials: 'include',
    });
    if (!res.ok) {
      throw new Error('Unauthenticated');
    }
    return res.json();
  },

  async getOrgUsers(): Promise<User[]> {
    const res = await fetch(`${API_BASE}/org-users`, {
      method: 'GET',
      headers: getHeaders(),
      credentials: 'include',
    });
    if (!res.ok) {
      throw new Error('Failed to fetch org users');
    }
    return res.json();
  },
};
