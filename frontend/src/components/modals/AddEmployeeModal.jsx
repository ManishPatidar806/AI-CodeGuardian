import React, { useState } from 'react';
import { X, UserPlus, Key, Mail, User } from 'lucide-react';
import { createEmployeeAccount } from '../../services/api';

export function AddEmployeeModal({ isOpen, onClose, onEmployeeCreated }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!name.trim() || !email.trim() || !username.trim() || !password) {
      setErrorMsg('Please complete all employee account fields.');
      return;
    }

    setLoading(true);
    const res = await createEmployeeAccount({
      name: name.trim(),
      email: email.trim(),
      username: username.trim(),
      password
    });
    setLoading(false);

    if (res.success) {
      onEmployeeCreated(res.user);
      setName('');
      setEmail('');
      setUsername('');
      setPassword('');
      onClose();
    } else {
      setErrorMsg(res.error || 'Failed to create employee account.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-lg shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-100">
        
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <UserPlus className="w-4 h-4 text-slate-700" />
            <h2 className="text-sm font-bold text-slate-900">
              Create Employee Account (Admin)
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-3.5 text-xs">
          
          <p className="text-slate-500 text-[11px]">
            Assign login credentials (username & password) for the new employee. They will use these to log into the self-hosted instance.
          </p>

          {errorMsg && (
            <div className="p-2.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. John Doe"
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. john.doe@company.com"
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Assigned Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. john_dev"
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Assigned Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono"
              required
            />
          </div>

          {/* Footer */}
          <div className="pt-3 border-t border-slate-100 flex justify-end gap-2">
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
              {loading ? 'Creating...' : '+ Create Employee Account'}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
