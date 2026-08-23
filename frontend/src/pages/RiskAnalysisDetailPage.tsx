import React, { useEffect, useState } from 'react';
import { Change, RiskAnalysis } from '../types';
import { api } from '../services/api';

interface Props {
  changeId: string;
  onBack: () => void;
}

export const RiskAnalysisDetailPage: React.FC<Props> = ({ changeId, onBack }) => {
  const [change, setChange] = useState<Change | null>(null);
  const [analysis, setAnalysis] = useState<RiskAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalysis();
  }, [changeId]);

  const loadAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const c = await api.getChange(changeId);
      setChange(c);

      try {
        const a = await api.getRiskAnalysis(changeId);
        setAnalysis(a);
      } catch {
        // If analysis is not ready yet, trigger analysis
        const a = await api.triggerAnalysis(changeId);
        setAnalysis(a);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load risk analysis');
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadge = (level?: string) => {
    switch (level) {
      case 'critical':
      case 'high':
        return <span className="px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 text-xs font-mono font-bold uppercase">CRITICAL / HIGH RISK</span>;
      case 'medium':
        return <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-mono font-bold uppercase">MEDIUM RISK</span>;
      default:
        return <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-mono font-bold uppercase">LOW RISK</span>;
    }
  };

  if (loading) {
    return (
      <div className="glass-card p-12 text-center text-xs text-slate-400 space-y-2">
        <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto" />
        <p>Running AI RAG Risk Assessment & Context Grounding...</p>
      </div>
    );
  }

  if (error || !change) {
    return (
      <div className="glass-card p-8 text-center space-y-4">
        <div className="text-rose-400 text-xs">{error || 'Change record not found'}</div>
        <button onClick={onBack} className="px-4 py-2 bg-slate-800 text-slate-300 rounded text-xs">
          ← Back to Changes
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Back Navigation Bar */}
      <div className="flex justify-between items-center">
        <button
          onClick={onBack}
          className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-xs font-medium transition-all"
        >
          ← Back to Deployment Changes
        </button>
        {analysis && getRiskBadge(analysis.risk_level)}
      </div>

      {/* Change Metadata Banner */}
      <div className="glass-card p-6 space-y-2 border-l-4 border-l-cyan-500">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-lg font-bold text-slate-100">{change.title}</h1>
            <p className="text-xs text-slate-400 font-mono mt-0.5">Submitted by author ID: {change.author_id || 'System'}</p>
          </div>
          <div className="text-right font-mono">
            <div className="text-xs text-slate-400">Risk Score</div>
            <div className="text-xl font-extrabold text-cyan-400">
              {change.risk_score !== undefined && change.risk_score !== null ? `${change.risk_score.toFixed(1)} / 10.0` : 'N/A'}
            </div>
          </div>
        </div>
        <p className="text-xs text-slate-300 bg-slate-900/60 p-3 rounded-lg border border-slate-800 leading-relaxed font-mono">
          {change.description}
        </p>
      </div>

      {/* Degraded Mode Warning Indicator */}
      {analysis?.is_degraded && (
        <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center space-x-2">
          <span className="font-bold">⚠️ DEGRADED MODE:</span>
          <span>Analysis generated via local zero-cost heuristic engine (Mock Provider fallback).</span>
        </div>
      )}

      {/* Side-by-Side Summaries: Technical (SREs) vs Business (Executives) */}
      {analysis && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Technical Summary Card */}
          <div className="glass-card p-6 space-y-3 border-t-2 border-t-cyan-500">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">🛠️ Technical Summary (SRE & Engineering)</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{analysis.technical_summary}</p>
          </div>

          {/* Business Summary Card */}
          <div className="glass-card p-6 space-y-3 border-t-2 border-t-violet-500">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <span className="text-xs font-mono font-bold text-violet-400 uppercase tracking-wider">💼 Business Summary (Executives & Ops)</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{analysis.business_summary}</p>
          </div>
        </div>
      )}

      {/* Recommended Action Checklist */}
      {analysis?.recommendations && analysis.recommendations.length > 0 && (
        <div className="glass-card p-6 space-y-4">
          <h2 className="text-sm font-bold text-slate-200">Recommended Action Checklist</h2>
          <div className="space-y-2">
            {analysis.recommendations.map((rec, idx) => (
              <div key={idx} className="flex items-start space-x-3 p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-cyan-400 font-mono text-xs font-bold">{idx + 1}.</span>
                <span className="text-xs text-slate-300 leading-relaxed">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
