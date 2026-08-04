import React, { useState } from 'react';
import { X, LogIn, Lock } from 'lucide-react';
import { loginUser } from '../../services/api';

export function AuthModal({ isOpen, onClose, currentUser, onSelectUser }) {
  // Login Form State
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!loginUsername.trim() || !loginPassword) {
      setErrorMsg('Please enter both username and password.');
      return;
    }

    setLoading(true);
    const res = await loginUser({
      username: loginUsername.trim(),
      password: loginPassword
    });
    setLoading(false);

    if (res.success) {
      onSelectUser({
        ...res.user,
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(res.user.name)}&background=0f172a&color=fff`
      });
      onClose();
    } else {
      setErrorMsg(res.error || 'Invalid credentials.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-lg shadow-xl w-full max-w-sm overflow-hidden animate-in fade-in zoom-in-95 duration-100">
        
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2 font-bold text-slate-900 text-sm">
            <LogIn className="w-4 h-4 text-slate-700" />
            <span>Self-Hosted Instance Login</span>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLoginSubmit} className="p-5 space-y-3.5 text-xs">
          <p className="text-[11px] text-slate-500">
            Log in using your assigned credentials. First-time deployment uses default admin credentials (<code className="font-bold">admin</code> / <code className="font-bold">adminpassword</code>).
          </p>

          {errorMsg && (
            <div className="p-2 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Username
            </label>
            <input
              type="text"
              value={loginUsername}
              onChange={(e) => setLoginUsername(e.target.value)}
              placeholder="e.g. admin"
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono"
              required
            />
          </div>

          <div className="pt-2 text-[10px] text-slate-400 bg-slate-50 p-2.5 rounded border border-slate-100 space-y-1">
            <div className="font-bold text-slate-700">💡 Default Server Credentials:</div>
            <div>Admin: <code className="text-slate-900 font-bold">admin</code> / <code className="text-slate-900 font-bold">adminpassword</code></div>
          </div>

          <div className="pt-2 border-t border-slate-100 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-slate-900 rounded hover:bg-slate-800 transition-colors shadow-sm disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
