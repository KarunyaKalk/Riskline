import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export const validatePassword = (password: string): string | null => {
  if (password.length < 8) return 'Password must be at least 8 characters long.';
  if (!/[A-Z]/.test(password)) return 'Password must contain at least 1 uppercase letter (A-Z).';
  if (!/[a-z]/.test(password)) return 'Password must contain at least 1 lowercase letter (a-z).';
  if (!/[0-9]/.test(password)) return 'Password must contain at least 1 number (0-9).';
  if (!/[-!@#$%^&*()_+={}\[\]:;\"'<>,.?/|\\]/.test(password)) return 'Password must contain at least 1 special character (e.g. -, _, !, @, #, $, %).';
  return null;
};

export const validateEmail = (email: string): string | null => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) return 'Please enter a valid email address.';
  return null;
};

export const LoginPage: React.FC<{ onSwitchToSignup: () => void }> = ({ onSwitchToSignup }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const emailErr = validateEmail(email);
    if (emailErr) {
      setError(emailErr);
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4 font-sans">
      <div className="w-full max-w-md glass-card p-8 space-y-6">
        <div className="text-center">
          <div className="inline-block p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 mb-3">
            <span className="text-cyan-400 font-mono font-bold text-xl">⚡ RISK-OS</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100">Sign in to Mission Control</h2>
          <p className="text-xs text-slate-400 mt-1">Multi-Tenant DevOps Risk & AI Assessment Platform</p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs text-center leading-relaxed">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Work Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="engineer@company.com"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold text-xs rounded-lg transition-all shadow-md"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div className="text-center pt-2 border-t border-slate-800">
          <p className="text-xs text-slate-400">
            Need an organization account?{' '}
            <button onClick={onSwitchToSignup} className="text-cyan-400 hover:underline font-medium">
              Create Organization
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export const SignupPage: React.FC<{ onSwitchToLogin: () => void }> = ({ onSwitchToLogin }) => {
  const { signup } = useAuth();
  const [orgName, setOrgName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const emailErr = validateEmail(email);
    if (emailErr) {
      setError(emailErr);
      return;
    }

    const passErr = validatePassword(password);
    if (passErr) {
      setError(passErr);
      return;
    }

    setLoading(true);
    try {
      await signup(orgName, email, password);
    } catch (err: any) {
      setError(err.message || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4 font-sans">
      <div className="w-full max-w-md glass-card p-8 space-y-6">
        <div className="text-center">
          <h2 className="text-xl font-bold text-slate-100">Create New Organization</h2>
          <p className="text-xs text-slate-400 mt-1">Setup multi-tenant workspace & Admin account</p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs text-center leading-relaxed">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Organization Name</label>
            <input
              type="text"
              required
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="Acme Engineering"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Admin Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@acme.com"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-xs font-medium text-slate-300">Password</label>
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus-visible:ring-2 focus-visible:ring-cyan-500"
            />
            <p className="text-[10px] text-slate-500 mt-1 font-mono">
              Restraints: Min 8 chars, 1 uppercase (A-Z), 1 number (0-9), 1 special char (-, _, !, @, #, $, %)
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition-all shadow-md"
          >
            {loading ? 'Creating Organization...' : 'Provision Organization'}
          </button>
        </form>

        <div className="text-center pt-2 border-t border-slate-800">
          <p className="text-xs text-slate-400">
            Already have an account?{' '}
            <button onClick={onSwitchToLogin} className="text-cyan-400 hover:underline font-medium">
              Sign In
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};
