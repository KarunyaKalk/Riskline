import React, { useEffect, useState } from 'react';
import { Note } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const NotesPage: React.FC = () => {
  const { user } = useAuth();
  const [notes, setNotes] = useState<Note[]>([]);
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New Note state
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState<string>('idea');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadNotes();
  }, [selectedTag]);

  const loadNotes = async () => {
    setLoading(true);
    try {
      const data = await api.listNotes(selectedTag);
      setNotes(data.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNote = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    const tagList = tags.split(',').map((t) => t.trim()).filter(Boolean);

    // Optimistic UI update
    const tempNote: Note = {
      id: Date.now().toString(),
      org_id: user?.org_id || '',
      title,
      content,
      author_id: user?.id,
      tags: tagList,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setNotes((prev) => [tempNote, ...prev]);
    setIsModalOpen(false);
    setTitle('');
    setContent('');

    try {
      const created = await api.createNote({ title, content, tags: tagList });
      setNotes((prev) => prev.map((n) => (n.id === tempNote.id ? created : n)));
    } catch (err) {
      console.error('Failed to create note, rolling back', err);
      setNotes((prev) => prev.filter((n) => n.id !== tempNote.id));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteNote = async (id: string) => {
    const backup = [...notes];
    setNotes((prev) => prev.filter((n) => n.id !== id));
    try {
      await api.deleteNote(id);
    } catch (err) {
      console.error('Failed to delete note, rolling back', err);
      setNotes(backup);
    }
  };

  const getTagBadgeColor = (tag: string) => {
    switch (tag.toLowerCase()) {
      case 'blocker':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'decision':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'question':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      default:
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Team Notes & Brainstorm Board</h1>
          <p className="text-xs text-slate-400 mt-0.5">Post architectural decisions, blockers, ideas, or incident questions</p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs rounded-lg transition-all shadow-md"
        >
          + Post New Note
        </button>
      </div>

      {/* Tag Filters */}
      <div className="flex space-x-2 border-b border-slate-800 pb-2">
        {['all', 'idea', 'blocker', 'decision', 'question'].map((t) => (
          <button
            key={t}
            onClick={() => setSelectedTag(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all ${
              selectedTag === t
                ? 'bg-slate-800 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Notes Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400">Loading notes board...</div>
      ) : notes.length === 0 ? (
        <div className="glass-card p-12 text-center text-xs text-slate-400">No notes found for tag '{selectedTag}'</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {notes.map((n) => {
            const canDelete = n.author_id === user?.id || user?.role === 'admin';
            return (
              <div key={n.id} className="glass-card p-5 flex flex-col justify-between space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between items-start">
                    <h3 className="font-bold text-sm text-slate-100 leading-snug">{n.title}</h3>
                    {canDelete && (
                      <button
                        onClick={() => handleDeleteNote(n.id)}
                        className="text-slate-500 hover:text-rose-400 text-xs px-1.5 py-0.5 rounded"
                        title="Delete Note"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{n.content}</p>
                </div>

                <div className="flex justify-between items-center pt-3 border-t border-slate-800/80">
                  <div className="flex flex-wrap gap-1">
                    {(n.tags || []).map((tg, i) => (
                      <span
                        key={i}
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${getTagBadgeColor(tg)}`}
                      >
                        #{tg}
                      </span>
                    ))}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(n.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Note Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md glass-card p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-bold text-sm text-slate-100">Post Note to Brainstorm Board</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-200 text-xs">
                Close
              </button>
            </div>

            <form onSubmit={handleCreateNote} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Postgres DB Migration Blocker"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Tag Category</label>
                <select
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus-visible:ring-2 focus-visible:ring-cyan-500"
                >
                  <option value="idea">idea</option>
                  <option value="blocker">blocker</option>
                  <option value="decision">decision</option>
                  <option value="question">question</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Content</label>
                <textarea
                  rows={4}
                  required
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Describe context or proposal..."
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
                />
              </div>

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
                  className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs rounded-lg transition-all"
                >
                  {submitting ? 'Posting...' : 'Post Note'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
