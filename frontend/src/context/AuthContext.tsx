import React, { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../api/auth';
import { LoginPayload, Organization, SignupPayload, User } from '../types';

interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  signup: (payload: SignupPayload) => Promise<void>;
  logout: () => Promise<void>;
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

  const login = async (payload: LoginPayload) => {
    const data = await authApi.login(payload);
    setUser(data.user);
    setOrganization(data.organization);
  };

  const signup = async (payload: SignupPayload) => {
    const data = await authApi.signup(payload);
    setUser(data.user);
    setOrganization(data.organization);
  };

  const logout = async () => {
    await authApi.logout();
    setUser(null);
    setOrganization(null);
  };

  return (
    <AuthContext.Provider value={{ user, organization, loading, login, signup, logout }}>
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
