import React, { useEffect, useState } from 'react';
import { OrgInvite, UserRole } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const OrgSettingsPage: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<UserRole>('engineer');
  const [generatedInvite, setGeneratedInvite] = useState<OrgInvite | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const inv = await api.createInvite({ email: inviteEmail, role: inviteRole });
      setGeneratedInvite(inv);
      setInviteEmail('');
    } catch (err: any) {
      setError(err.message || 'Failed to generate invite');
    } finally {
      setLoading(false);
    }
  };

  const copyInviteLink = (token: string) => {
    const link = `${window.location.origin}/accept-invite?token=${token}`;
    navigator.clipboard.writeText(link);
    alert(`Copied 48-hr invite link to clipboard:\n${link}`);
  };

  if (!isAdmin) {
    return (
      <div className="glass-card p-8 text-center text-xs text-rose-400">
        Organization Settings and Invite Management are restricted to Admin role accounts.
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Organization Settings & Invites</h1>
        <p className="text-xs text-slate-400 mt-0.5">Manage teammate invitations, user roles, and delivery settings</p>
      </div>

      {/* Invite Teammate Card */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-bold text-slate-200">Issue Teammate Invitation Link</h2>

        {error && (
          <div className="p-3 rounded bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleGenerateInvite} className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Recipient Email</label>
            <input
              type="email"
              required
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="newmember@company.com"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus-visible:ring-2 focus-visible:ring-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Assigned Role</label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as UserRole)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus-visible:ring-2 focus-visible:ring-cyan-500"
            >
              <option value="engineer">Engineer</option>
              <option value="business_ops">Business Ops</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading || !inviteEmail.trim()}
            className="py-2 px-4 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs rounded-lg transition-all"
          >
            {loading ? 'Generating...' : 'Issue 48-Hr Invite Token'}
          </button>
        </form>

        {generatedInvite && (
          <div className="p-4 rounded-lg bg-cyan-950/40 border border-cyan-500/40 space-y-2 mt-4">
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-cyan-300">Invite Issued Successfully!</span>
              <span className="text-[10px] font-mono text-slate-400">Expires in 48 Hours</span>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                readOnly
                value={`${window.location.origin}/accept-invite?token=${generatedInvite.token}`}
                className="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-300 font-mono"
              />
              <button
                onClick={() => copyInviteLink(generatedInvite.token)}
                className="px-3 py-1.5 bg-cyan-500 text-slate-950 font-semibold text-xs rounded"
              >
                Copy Link
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Governance & Role Rules Card */}
      <div className="glass-card p-6 space-y-3">
        <h2 className="text-sm font-bold text-slate-200">Tenant Security & Sole-Admin Governance</h2>
        <p className="text-xs text-slate-400 leading-relaxed">
          Organizational tenant isolation is strictly enforced at the database level (`org_id` column mixin).
          Demoting or deleting the sole active Admin account is blocked by backend demotion protection rules.
        </p>
      </div>
    </div>
  );
};
