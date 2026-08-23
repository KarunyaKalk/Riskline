export type UserRole = 'admin' | 'engineer' | 'business_ops' | 'viewer';

export interface User {
  id: string;
  org_id: string;
  email: string;
  role: UserRole;
  status: string;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  created_at: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface SignupPayload {
  org_name: string;
  email: string;
  password: string;
  name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  organization?: Organization;
}

export interface UserMeResponse {
  user: User;
  organization: Organization;
}

export interface Change {
  id: string;
  org_id: string;
  title: string;
  description: string;
  status: 'pending' | 'processing' | 'analyzed' | 'deployed' | 'rolled_back';
  author_id?: string;
  deployment_date?: string;
  risk_score?: number;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface RiskAnalysis {
  id: string;
  org_id: string;
  change_id: string;
  technical_summary: string;
  business_summary: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_score?: number;
  recommendations: string[];
  is_degraded: boolean;
  created_at: string;
}

export interface Note {
  id: string;
  org_id: string;
  title: string;
  content: string;
  author_id?: string;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  org_id: string;
  user_id?: string;
  name: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}

export interface ProjectProgress {
  id: string;
  org_id: string;
  title: string;
  status: string;
  progress_pct: number;
  owner_id?: string;
  target_date?: string;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  org_id: string;
  user_id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  target_url?: string;
  created_at: string;
}

export interface NotificationPreference {
  user_id: string;
  inapp_enabled: boolean;
  email_enabled: boolean;
  slack_enabled: boolean;
  min_risk_level: string;
}

export interface ChatMessage {
  id: string;
  org_id: string;
  user_id?: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface AuditLog {
  id: string;
  org_id: string;
  actor_user_id?: string;
  action: string;
  target_type: string;
  target_id?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface OrgInvite {
  id: string;
  org_id: string;
  email: string;
  role: UserRole;
  token: string;
  status: string;
  expires_at: string;
  created_at: string;
}
