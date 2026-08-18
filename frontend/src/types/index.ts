export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  created_at: string;
}

export type UserRole = 'admin' | 'engineer' | 'business_ops' | 'viewer';

export interface User {
  id: string;
  org_id: string;
  email: string;
  role: UserRole;
  status: string;
  created_at: string;
}

export interface AuthResponse {
  user: User;
  organization: Organization;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserMeResponse {
  user: User;
  organization: Organization;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface SignupPayload {
  org_name: string;
  email: string;
  password: string;
}
