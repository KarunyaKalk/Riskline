import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Header } from './components/Header';
import { Navigation } from './components/Navigation';
import { ChatDrawer } from './components/ChatDrawer';
import { LoginPage, SignupPage } from './pages/AuthPages';
import { InviteAcceptPage } from './pages/InviteAcceptPage';
import { DashboardPage } from './pages/DashboardPage';
import { ChangesPage } from './pages/ChangesPage';
import { RiskAnalysisDetailPage } from './pages/RiskAnalysisDetailPage';
import { NotesPage } from './pages/NotesPage';
import { TeamRosterPage } from './pages/TeamRosterPage';
import { OrgSettingsPage } from './pages/OrgSettingsPage';
import { AuditLogsPage } from './pages/AuditLogsPage';

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedChangeId, setSelectedChangeId] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Check if current URL is accept-invite
  if (window.location.pathname === '/accept-invite') {
    return <InviteAcceptPage />;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-xs font-mono text-cyan-400">
        Initializing DevOps Risk Mission Control...
      </div>
    );
  }

  if (!user) {
    return authMode === 'login' ? (
      <LoginPage onSwitchToSignup={() => setAuthMode('signup')} />
    ) : (
      <SignupPage onSwitchToLogin={() => setAuthMode('login')} />
    );
  }

  const handleSelectChange = (id: string) => {
    setSelectedChangeId(id);
    setActiveTab('change-detail');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header
        onToggleChat={() => setIsChatOpen(!isChatOpen)}
        onNavigate={(path) => {
          if (path.startsWith('/changes/')) {
            const id = path.replace('/changes/', '');
            handleSelectChange(id);
          }
        }}
      />

      <div className="flex-1 flex">
        <Navigation
          activeTab={activeTab === 'change-detail' ? 'changes' : activeTab}
          onTabChange={(tab) => {
            setActiveTab(tab);
            if (tab !== 'change-detail') setSelectedChangeId(null);
          }}
        />

        <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
          {activeTab === 'dashboard' && <DashboardPage onSelectChange={handleSelectChange} />}
          {activeTab === 'changes' && <ChangesPage onSelectChange={handleSelectChange} />}
          {activeTab === 'change-detail' && selectedChangeId && (
            <RiskAnalysisDetailPage
              changeId={selectedChangeId}
              onBack={() => {
                setActiveTab('changes');
                setSelectedChangeId(null);
              }}
            />
          )}
          {activeTab === 'notes' && <NotesPage />}
          {activeTab === 'roster' && <TeamRosterPage />}
          {activeTab === 'settings' && <OrgSettingsPage />}
          {activeTab === 'audit' && <AuditLogsPage />}
        </main>
      </div>

      <ChatDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
