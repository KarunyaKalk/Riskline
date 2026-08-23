import React, { useEffect, useState } from 'react';
import { Change } from '../types';
import { api } from '../services/api';

interface Props {
  onSelectChange: (id: string) => void;
}

export const ChangesPage: React.FC<Props> = ({ onSelectChange }) => {
  const [changes, setChanges] = useState<Change[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New Change Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadChanges();
  }, [statusFilter]);

  const loadChanges = async () => {
    setLoading(true);
    try {
      const data = await api.listChanges(statusFilter === 'all' ? undefined : statusFilter);
      setChanges(data.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (pdfFile) {
        await api.uploadPdfChange(pdfFile, title || pdfFile.name);
      } else {
        await api.createChange({ title, description });
      }
      setIsModalOpen(false);
      setTitle('');
      setDescription('');
      setPdfFile(null);
      loadChanges();
    } catch (err: any) {
      setError(err.message || 'Failed to submit change');
    } finally {
      setSubmitting(false);
    }
  };

  const getRiskScoreBadge = (score?: number) => {
    if (score === undefined || score === null) {
      return <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-amber-300 border border-amber-500/30 animate-pulse">Processing...</span>;
    }
    if (score >= 7.0) {
      return <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full font-bold text-rose-400 bg-rose-500/20 border border-rose-500/30">{score.toFixed(1)} / 10 (HIGH)</span>;
    }
    if (score >= 4.0) {
      return <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full font-bold text-amber-400 bg-amber-500/20 border border-amber-500/30">{score.toFixed(1)} / 10 (MED)</span>;
    }
    return <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full font-bold text-emerald-400 bg-emerald-500/20 border border-emerald-500/30">{score.toFixed(1)} / 10 (LOW)</span>;
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Deployment Changes & Risk Engine</h1>
          <p className="text-xs text-slate-400 mt-0.5">Submit architecture updates or upload PDF specs for AI risk evaluation</p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs rounded-lg transition-all shadow-md flex items-center space-x-2"
        >
          <span>+ Submit New Change</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 border-b border-slate-800 pb-2">
        {['all', 'pending', 'analyzed', 'deployed'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
              statusFilter === st
                ? 'bg-slate-800 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Changes Table */}
      <div className="glass-card p-5">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading changes...</div>
        ) : changes.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">No deployment changes found for filter '{statusFilter}'</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono">
                  <th className="pb-3">Title / Summary</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3">Risk Assessment</th>
                  <th className="pb-3">Created Date</th>
                  <th className="pb-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {changes.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/50 transition-colors">
                    <td className="py-3.5 pr-4">
                      <div className="font-semibold text-slate-200">{c.title}</div>
                      <div className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{c.description}</div>
                    </td>
                    <td className="py-3.5">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3.5">{getRiskScoreBadge(c.risk_score)}</td>
                    <td className="py-3.5 text-slate-500 font-mono text-[11px]">
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 text-right">
                      <button
                        onClick={() => onSelectChange(c.id)}
                        className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded text-xs font-medium transition-all"
                      >
                        View Risk Breakdown
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Submit Change Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg glass-card p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-bold text-sm text-slate-100">Submit Deployment Change</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-200 text-xs">
                Close
              </button>
            </div>

            {error && (
              <div className="p-3 rounded bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Change Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Upgrade Postgres DB Schema / Refactor Auth Middleware"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Upload PDF Specification (Optional)</label>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-slate-800 file:text-cyan-400 hover:file:bg-slate-700"
                />
              </div>

              {!pdfFile && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Deployment Description & Architectural Details</label>
                  <textarea
                    rows={4}
                    required={!pdfFile}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Provide migration details, SQL queries, infrastructure changes, or code diffs..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
                  />
                </div>
              )}

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs rounded-lg transition-all"
                >
                  {submitting ? 'Submitting & Indexing...' : 'Submit Change for Risk Analysis'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
