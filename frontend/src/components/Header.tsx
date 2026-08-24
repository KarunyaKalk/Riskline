import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { NotificationPopover } from './NotificationPopover';
import { api } from '../services/api';

interface HeaderProps {
  onToggleChat: () => void;
  onNavigate?: (path: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleChat, onNavigate }) => {
  const { user, logout } = useAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [liveConnected, setLiveConnected] = useState(true);

  useEffect(() => {
    fetchUnreadCount();
    // Subscribe to SSE stream for live events
    const es = new EventSource('/api/v1/events/stream');
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'HIGH_RISK_NOTIFICATION') {
          setUnreadCount((prev) => prev + 1);
        }
      } catch (e) {
        console.error(e);
      }
    };
    es.onopen = () => setLiveConnected(true);
    es.onerror = () => setLiveConnected(false);

    return () => {
      es.close();
    };
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const data = await api.listNotifications();
      setUnreadCount(data.unread_count);
    } catch {
      // Ignore
    }
  };

  const getRoleBadgeColor = (role?: string) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'engineer':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case 'business_ops':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-700/50 text-slate-300 border-slate-600';
    }
  };

  return (
    <header className="h-16 bg-slate-900/90 border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md">
      <div className="flex items-center space-x-4">
        <span className="text-xs font-mono tracking-wider text-slate-400 uppercase">
          DevOps Risk Mission Control
        </span>
        <div className="flex items-center space-x-2 bg-slate-800/60 px-2.5 py-1 rounded-full border border-slate-700/60">
          <span
            className={`w-2 h-2 rounded-full ${
              liveConnected ? 'bg-emerald-400 animate-live-dot' : 'bg-amber-400'
            }`}
          />
          <span className="text-[11px] font-mono text-slate-300">
            {liveConnected ? 'LIVE FEED ACTIVE' : 'RECONNECTING'}
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Chat Drawer Toggle Button */}
        <button
          onClick={onToggleChat}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-violet-600/20 hover:bg-violet-600/30 border border-violet-500/40 text-violet-300 text-xs font-medium transition-all shadow-sm focus-visible:ring-2"
          aria-label="Toggle AI Risk Assistant Drawer"
        >
          <svg className="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span>AI Risk Assistant</span>
        </button>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setIsNotifOpen(!isNotifOpen)}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 relative transition-all focus-visible:ring-2"
            aria-label="View notifications"
          >
            <svg className="w-4 h-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-rose-500 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center animate-bounce">
                {unreadCount}
              </span>
            )}
          </button>
          <NotificationPopover
            isOpen={isNotifOpen}
            onClose={() => setIsNotifOpen(false)}
            onSelectNotification={(url) => {
              setIsNotifOpen(false);
              if (url && onNavigate) onNavigate(url);
            }}
          />
        </div>

        {/* User Info & Logout */}
        <div className="flex items-center space-x-3 border-l border-slate-800 pl-4">
          <div className="text-right">
            <div className="text-xs font-medium text-slate-200">{user?.email}</div>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${getRoleBadgeColor(user?.role)} uppercase`}>
              {user?.role}
            </span>
          </div>
          <button
            onClick={logout}
            className="text-xs text-slate-400 hover:text-rose-400 transition-colors p-1"
            title="Sign Out"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};
