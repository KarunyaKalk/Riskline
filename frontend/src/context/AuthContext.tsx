import React, { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../api/auth';
import { Organization, User } from '../types';

interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (orgName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setAuthState: (user: User, token: string, org?: Organization) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const data = await authApi.getMe();
        setUser(data.user);
        setOrganization(data.organization);
      } catch (err) {
        setUser(null);
        setOrganization(null);
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await authApi.login({ email, password });
    setUser(data.user);
    if (data.organization) setOrganization(data.organization);
  };

  const signup = async (orgName: string, email: string, password: string) => {
    const data = await authApi.signup({ org_name: orgName, email, password });
    setUser(data.user);
    if (data.organization) setOrganization(data.organization);
  };

  const logout = async () => {
    await authApi.logout();
    setUser(null);
    setOrganization(null);
  };

  const setAuthState = (user: User, token: string, org?: Organization) => {
    localStorage.setItem('access_token', token);
    setUser(user);
    if (org) setOrganization(org);
  };

  return (
    <AuthContext.Provider value={{ user, organization, loading, login, signup, logout, setAuthState }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
