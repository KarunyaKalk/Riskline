import React, { useEffect, useState } from 'react';
import { Notification } from '../types';
import { api } from '../services/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelectNotification?: (url?: string) => void;
}

export const NotificationPopover: React.FC<Props> = ({ isOpen, onClose, onSelectNotification }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadNotifications();
    }
  }, [isOpen]);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await api.listNotifications();
      setNotifications(data.items);
    } catch (e) {
      console.error('Failed to load notifications', e);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id: string, url?: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
      if (onSelectNotification && url) {
        onSelectNotification(url);
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="absolute right-0 mt-2 w-96 glass-card border border-slate-700 shadow-2xl z-50 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-700 flex justify-between items-center bg-slate-900/60">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-sm text-slate-100">Notifications</span>
          <span className="text-xs bg-cyan-500/20 text-cyan-400 px-2 py-0.5 rounded-full font-mono">
            {notifications.filter((n) => !n.is_read).length} unread
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 text-xs px-2 py-1 rounded bg-slate-800"
        >
          Close
        </button>
      </div>

      <div className="max-h-80 overflow-y-auto divide-y divide-slate-800">
        {loading ? (
          <div className="p-6 text-center text-xs text-slate-400">Loading alerts...</div>
        ) : notifications.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400">No high-risk notifications</div>
        ) : (
          notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => handleMarkRead(n.id, n.target_url)}
              className={`p-3.5 cursor-pointer transition-colors ${
                n.is_read ? 'bg-slate-900/30 hover:bg-slate-800/40' : 'bg-red-950/20 hover:bg-red-900/30 border-l-2 border-rose-500'
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-medium text-slate-200">{n.title}</span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{n.message}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
