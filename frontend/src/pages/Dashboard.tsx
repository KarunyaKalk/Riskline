import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/auth';
import { User } from '../types';

export const Dashboard: React.FC = () => {
  const { user, organization, logout } = useAuth();
  const navigate = useNavigate();
  const [orgUsers, setOrgUsers] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);

  useEffect(() => {
    const loadOrgUsers = async () => {
      try {
        const users = await authApi.getOrgUsers();
        setOrgUsers(users);
      } catch (err) {
        console.error('Failed to load org users', err);
      } finally {
        setLoadingUsers(false);
      }
    };
    loadOrgUsers();
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.appTitle}>DevOps Change Intelligence</h1>
          <span style={styles.orgBadge}>{organization?.name || 'Organization'}</span>
        </div>
        <div style={styles.headerRight}>
          <div style={styles.userMeta}>
            <span style={styles.userEmail}>{user?.email}</span>
            <span style={styles.roleBadge}>{user?.role}</span>
          </div>
          <button onClick={handleLogout} style={styles.logoutButton}>
            Sign Out
          </button>
        </div>
      </header>

      <main style={styles.main}>
        <div style={styles.cardGrid}>
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>Tenant Profile</h3>
            <div style={styles.infoRow}>
              <span style={styles.infoLabel}>Organization Name:</span>
              <span style={styles.infoValue}>{organization?.name}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.infoLabel}>Org Slug:</span>
              <span style={styles.infoValue}>{organization?.slug}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.infoLabel}>Subscription Tier:</span>
              <span style={styles.infoValue}>{organization?.plan}</span>
            </div>
          </div>

          <div style={styles.card}>
            <h3 style={styles.cardTitle}>User Session</h3>
            <div style={styles.infoRow}>
              <span style={styles.infoLabel}>User ID:</span>
              <span style={styles.infoValue}>{user?.id}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.infoLabel}>Role:</span>
              <span style={styles.infoValue}>{user?.role}</span>
            </div>
            <div style={styles.infoRow}>
              <span style={styles.infoLabel}>Status:</span>
              <span style={styles.infoValue}>{user?.status}</span>
            </div>
          </div>
        </div>

        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Organization Users ({orgUsers.length})</h2>
          {loadingUsers ? (
            <p style={{ color: '#94a3b8' }}>Loading tenant users...</p>
          ) : (
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>Email</th>
                  <th style={styles.th}>Role</th>
                  <th style={styles.th}>Status</th>
                  <th style={styles.th}>Created</th>
                </tr>
              </thead>
              <tbody>
                {orgUsers.map((u) => (
                  <tr key={u.id} style={styles.tr}>
                    <td style={styles.td}>{u.email}</td>
                    <td style={styles.td}>
                      <span style={styles.roleTag}>{u.role}</span>
                    </td>
                    <td style={styles.td}>{u.status}</td>
                    <td style={styles.td}>{new Date(u.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Dashboard Core Features (Day 2-7 Shell)</h2>
          <div style={styles.placeholderBox}>
            <p style={{ margin: 0, color: '#94a3b8' }}>
              Multi-tenant auth & core schema active. Additional modules (Change Data Ingestion, Risk Assessment Pipeline, Shared Dashboard, and Chatbot) will populate here.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#0f172a',
    color: '#f8fafc',
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 32px',
    backgroundColor: '#1e293b',
    borderBottom: '1px solid #334155',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  appTitle: {
    margin: 0,
    fontSize: '20px',
    fontWeight: 600,
  },
  orgBadge: {
    backgroundColor: '#3b82f6',
    color: '#ffffff',
    fontSize: '12px',
    fontWeight: 600,
    padding: '4px 10px',
    borderRadius: '12px',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
  },
  userMeta: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
  },
  userEmail: {
    fontSize: '14px',
    fontWeight: 500,
  },
  roleBadge: {
    fontSize: '11px',
    color: '#94a3b8',
    textTransform: 'uppercase',
  },
  logoutButton: {
    padding: '8px 16px',
    backgroundColor: 'transparent',
    border: '1px solid #475569',
    borderRadius: '6px',
    color: '#cbd5e1',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: 500,
  },
  main: {
    padding: '32px',
    maxWidth: '1100px',
    margin: '0 auto',
  },
  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '20px',
    marginBottom: '32px',
  },
  card: {
    backgroundColor: '#1e293b',
    borderRadius: '8px',
    padding: '20px',
    border: '1px solid #334155',
  },
  cardTitle: {
    margin: '0 0 16px 0',
    fontSize: '16px',
    color: '#38bdf8',
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    borderBottom: '1px solid #334155',
    fontSize: '14px',
  },
  infoLabel: {
    color: '#94a3b8',
  },
  infoValue: {
    fontWeight: 500,
  },
  section: {
    marginBottom: '32px',
  },
  sectionTitle: {
    fontSize: '18px',
    marginBottom: '16px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: '#1e293b',
    borderRadius: '8px',
    overflow: 'hidden',
    border: '1px solid #334155',
  },
  th: {
    textAlign: 'left',
    padding: '12px 16px',
    backgroundColor: '#0f172a',
    color: '#94a3b8',
    fontSize: '13px',
    fontWeight: 600,
  },
  td: {
    padding: '12px 16px',
    borderTop: '1px solid #334155',
    fontSize: '14px',
  },
  tr: {
    backgroundColor: '#1e293b',
  },
  roleTag: {
    padding: '2px 8px',
    backgroundColor: '#334155',
    borderRadius: '4px',
    fontSize: '12px',
  },
  placeholderBox: {
    padding: '24px',
    backgroundColor: '#1e293b',
    borderRadius: '8px',
    border: '1px dashed #475569',
  },
};

export default Dashboard;
