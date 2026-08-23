import React, { useEffect, useState } from 'react';
import { AuditLog } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const AuditLogsPage: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');

  useEffect(() => {
    if (isAdmin) {
      loadAuditLogs();
    }
  }, [actionFilter, isAdmin]);

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const data = await api.listAuditLogs(actionFilter || undefined);
      setLogs(data.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className="glass-card p-8 text-center text-xs text-rose-400">
        Audit Logs view is restricted to Admin role accounts.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Security & Mutation Audit Logs</h1>
          <p className="text-xs text-slate-400 mt-0.5">Immutable record of all org mutations, auth events, and role updates</p>
        </div>

        <input
          type="text"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          placeholder="Filter by action (e.g. CHANGE_CREATED)..."
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 w-64 focus-visible:ring-2 focus-visible:ring-cyan-500"
        />
      </div>

      <div className="glass-card p-5">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading audit trail...</div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">No audit logs found</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono">
                  <th className="pb-3">Action Event</th>
                  <th className="pb-3">Actor User ID</th>
                  <th className="pb-3">Target Type</th>
                  <th className="pb-3">Target ID</th>
                  <th className="pb-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="py-3 font-semibold text-cyan-400">{log.action}</td>
                    <td className="py-3 text-slate-400">{log.actor_user_id || 'System'}</td>
                    <td className="py-3 text-slate-300">{log.target_type}</td>
                    <td className="py-3 text-slate-400 truncate max-w-[150px]">{log.target_id || '-'}</td>
                    <td className="py-3 text-slate-500">{new Date(log.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
