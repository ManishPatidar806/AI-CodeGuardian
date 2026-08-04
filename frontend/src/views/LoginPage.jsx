import React, { useState } from 'react';
import { 
  Shield, 
  LogIn, 
  Lock, 
  User, 
  KeyRound, 
  ArrowRight,
  Sparkles,
  CheckCircle2
} from 'lucide-react';
import { loginUser } from '../services/api';

export function LoginPage({ onSelectUser }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('adminpassword');
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!username.trim() || !password) {
      setErrorMsg('Please enter both username and password.');
      return;
    }

    setLoading(true);
    const res = await loginUser({
      username: username.trim(),
      password
    });
    setLoading(false);

    if (res.success) {
      onSelectUser({
        ...res.user,
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(res.user.name)}&background=0f172a&color=fff`
      });
    } else {
      setErrorMsg(res.error || 'Invalid username or password.');
    }
  };

  const handleQuickFillAdmin = () => {
    setUsername('admin');
    setPassword('adminpassword');
    setErrorMsg('');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased flex flex-col justify-between selection:bg-slate-900 selection:text-white">
      {/* Top Header */}
      <header className="h-16 border-b border-slate-200 bg-white px-6 md:px-12 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-slate-900 text-white flex items-center justify-center font-bold shadow-xs">
            <Shield className="w-4.5 h-4.5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900 tracking-tight">
              AI CodeGuardian
            </h1>
            <span className="text-[10px] text-slate-400 font-mono">
              Enterprise Security Edition v2.5
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-md border border-slate-200">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Instance Status: Operational</span>
        </div>
      </header>

      {/* Main Centered Professional Login Card */}
      <main className="flex-1 max-w-md w-full mx-auto px-4 py-12 flex flex-col justify-center">
        <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-8 space-y-6">
          
          {/* Brand Icon & Heading */}
          <div className="text-center space-y-2">
            <div className="w-12 h-12 rounded-xl bg-slate-900 text-white flex items-center justify-center mx-auto shadow-md">
              <Shield className="w-6 h-6" />
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Sign in to AI CodeGuardian
            </h2>
            <p className="text-xs text-slate-500">
              Enter your enterprise account credentials to access your security dashboard.
            </p>
          </div>

          {/* Quick Auto-Fill Admin Credentials Preset */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-700 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-slate-900" />
                Default Admin Login
              </span>
              <button
                type="button"
                onClick={handleQuickFillAdmin}
                className="text-[11px] font-bold text-slate-900 hover:text-slate-700 underline cursor-pointer"
              >
                Auto-fill
              </button>
            </div>
            <div className="font-mono text-[11px] text-slate-600 flex items-center justify-between bg-white p-2 rounded border border-slate-200">
              <span>Username: <strong className="text-slate-900">admin</strong></span>
              <span>Password: <strong className="text-slate-900">adminpassword</strong></span>
            </div>
          </div>

          {/* Error Message */}
          {errorMsg && (
            <div className="p-3 rounded-md bg-rose-50 text-rose-700 border border-rose-200 text-xs font-medium text-center">
              {errorMsg}
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleLoginSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Username or Email Address
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. admin"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-900 focus:bg-white transition-all font-mono"
                  required
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-semibold text-slate-700">
                  Password
                </label>
              </div>
              <div className="relative">
                <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-900 focus:bg-white transition-all font-mono"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center gap-2 text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-300 text-slate-900 focus:ring-slate-900 accent-slate-900"
                />
                <span>Remember session</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-xs font-extrabold text-white bg-slate-900 rounded-md hover:bg-slate-800 transition-all shadow-sm cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <span>Authenticating Credentials...</span>
              ) : (
                <>
                  <span>Sign In to Dashboard</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Security Assurance Footer */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
            <span className="flex items-center gap-1 font-medium text-slate-500">
              <Lock className="w-3 h-3 text-emerald-600" /> TLS Encrypted Connection
            </span>
            <span>Self-Hosted Enterprise</span>
          </div>
        </div>
      </main>

      {/* Bottom Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 px-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-slate-900" />
            <span className="font-bold text-slate-900">AI CodeGuardian</span>
            <span>• Open Source Self-Hosted Platform</span>
          </div>

          <div className="text-[11px] text-slate-400">
            © 2026 AI CodeGuardian Inc. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
