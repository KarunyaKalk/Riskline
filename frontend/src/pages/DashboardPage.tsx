import React, { useEffect, useState } from 'react';
import { Change, ProjectProgress } from '../types';
import { api } from '../services/api';

interface Props {
  onSelectChange: (id: string) => void;
}

export const DashboardPage: React.FC<Props> = ({ onSelectChange }) => {
  const [changes, setChanges] = useState<Change[]>([]);
  const [progresses, setProgresses] = useState<ProjectProgress[]>([]);
  const [liveEvents, setLiveEvents] = useState<Array<{ type: string; title: string; time: string }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();

    // Subscribe to SSE stream for live activity
    const es = new EventSource('/api/v1/events/stream');
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type && data.type !== 'CONNECTED') {
          const newEvt = {
            type: data.type,
            title: data.payload?.title || data.type,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          };
          setLiveEvents((prev) => [newEvt, ...prev.slice(0, 9)]);
          // Refresh list data
          loadDashboardData();
        }
      } catch (e) {
        console.error(e);
      }
    };

    return () => {
      es.close();
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      const [cData, pData] = await Promise.all([api.listChanges(), api.listProgress()]);
      setChanges(cData.items);
      setProgresses(pData.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const totalChanges = changes.length;
  const highRiskCount = changes.filter((c) => (c.risk_score || 0) >= 7.0).length;
  const deployedCount = changes.filter((c) => c.status === 'deployed').length;
  const avgRiskScore =
    totalChanges > 0
      ? (changes.reduce((sum, c) => sum + (c.risk_score || 0), 0) / totalChanges).toFixed(1)
      : '0.0';

  const getRiskScoreColor = (score?: number) => {
    if (!score) return 'text-slate-400 bg-slate-800';
    if (score >= 7.0) return 'text-rose-400 bg-rose-500/20 border border-rose-500/30';
    if (score >= 4.0) return 'text-amber-400 bg-amber-500/20 border border-amber-500/30';
    return 'text-emerald-400 bg-emerald-500/20 border border-emerald-500/30';
  };

  return (
    <div className="space-y-6">
      {/* Top Header Title */}
      <div>
        <h1 className="text-xl font-bold text-slate-100">DevOps Risk Overview</h1>
        <p className="text-xs text-slate-400 mt-0.5">Real-time aggregate risk scores, milestones, and deployment activity</p>
      </div>

      {/* Aggregate Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-5">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Total Changes</div>
          <div className="text-2xl font-extrabold text-slate-100 mt-2">{totalChanges}</div>
          <div className="text-[11px] text-slate-500 mt-1">Across all environments</div>
        </div>

        <div className="glass-card p-5">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Avg Risk Score</div>
          <div className="text-2xl font-extrabold text-cyan-400 mt-2">{avgRiskScore} / 10</div>
          <div className="text-[11px] text-slate-500 mt-1">Weighted architectural risk</div>
        </div>

        <div className="glass-card p-5 border-l-4 border-l-rose-500">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">High Risk Alerts</div>
          <div className="text-2xl font-extrabold text-rose-400 mt-2">{highRiskCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Score ≥ 7.0 requires SRE review</div>
        </div>

        <div className="glass-card p-5 border-l-4 border-l-emerald-500">
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Deployed Releases</div>
          <div className="text-2xl font-extrabold text-emerald-400 mt-2">{deployedCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Successful production updates</div>
        </div>
      </div>

      {/* Main Grid: Recent Changes & Live SSE Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Changes Table (2 Cols) */}
        <div className="lg:col-span-2 glass-card p-5 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-bold text-slate-200">Recent Deployment Changes</h2>
            <span className="text-xs text-slate-400 font-mono">{changes.length} total</span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading metrics...</div>
          ) : changes.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">No deployment changes registered yet</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-mono">
                    <th className="pb-2">Title</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2">Risk Score</th>
                    <th className="pb-2">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {changes.slice(0, 6).map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => onSelectChange(c.id)}
                      className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                    >
                      <td className="py-3 font-medium text-slate-200">{c.title}</td>
                      <td className="py-3">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                          {c.status}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`text-[11px] font-mono px-2 py-0.5 rounded-full font-bold ${getRiskScoreColor(c.risk_score)}`}>
                          {c.risk_score !== undefined && c.risk_score !== null ? `${c.risk_score.toFixed(1)} / 10` : 'Pending'}
                        </span>
                      </td>
                      <td className="py-3 text-slate-500 font-mono text-[11px]">
                        {new Date(c.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Live SSE Stream Feed & Project Progress (1 Col) */}
        <div className="space-y-6">
          {/* Project Progress Tracker Widget */}
          <div className="glass-card p-5 space-y-4">
            <h2 className="text-sm font-bold text-slate-200">Project Milestones</h2>
            <div className="space-y-3">
              {progresses.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-4">No active milestones</div>
              ) : (
                progresses.slice(0, 4).map((p) => (
                  <div key={p.id} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-300 font-medium">{p.title}</span>
                      <span className="font-mono text-cyan-400">{p.progress_pct}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-cyan-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${p.progress_pct}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Real-time SSE Feed */}
          <div className="glass-card p-5 space-y-3">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              <h2 className="text-sm font-bold text-slate-200">Live Real-Time Stream</h2>
            </div>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {liveEvents.length === 0 ? (
                <div className="text-xs text-slate-500 text-center py-4">Listening for live updates...</div>
              ) : (
                liveEvents.map((evt, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
                    <div className="flex justify-between text-[10px] text-slate-500 font-mono mb-0.5">
                      <span className="text-cyan-400 font-semibold">{evt.type}</span>
                      <span>{evt.time}</span>
                    </div>
                    <p className="text-slate-300 font-medium truncate">{evt.title}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
