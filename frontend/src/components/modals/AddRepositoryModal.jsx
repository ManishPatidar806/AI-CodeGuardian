import React, { useState } from 'react';
import { X, FolderGit2, Check, Globe } from 'lucide-react';
import { registerRepository } from '../../services/api';

export function AddRepositoryModal({ isOpen, onClose, onRepositoryAdded }) {
  const [name, setName] = useState('');
  const [pathWithNamespace, setPathWithNamespace] = useState('');
  const [defaultBranch, setDefaultBranch] = useState('main');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!name.trim() || !pathWithNamespace.trim()) {
      setErrorMsg('Please enter repository name and public path namespace.');
      return;
    }

    // Standardize public repo format (e.g. org/repo or https://github.com/org/repo)
    let cleanedPath = pathWithNamespace.trim();
    if (cleanedPath.startsWith('https://github.com/')) {
      cleanedPath = cleanedPath.replace('https://github.com/', '');
    }

    setLoading(true);
    const res = await registerRepository({
      name: name.trim(),
      path_with_namespace: cleanedPath,
      default_branch: defaultBranch.trim() || 'main'
    });
    setLoading(false);

    if (res.success) {
      onRepositoryAdded(res.data);
      setName('');
      setPathWithNamespace('');
      onClose();
    } else {
      setErrorMsg(res.error || 'Failed to register repository.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-lg shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-100">
        
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <FolderGit2 className="w-4 h-4 text-slate-700" />
            <h2 className="text-sm font-bold text-slate-900">
              Connect Public Repository
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          
          <div className="p-3 rounded bg-sky-50 text-sky-800 border border-sky-100 flex items-start gap-2 text-[11px]">
            <Globe className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Public Repository Access: </span>
              AI CodeGuardian connects to public GitHub/GitLab repositories for automated PR reviews and vulnerability scans.
            </div>
          </div>

          {errorMsg && (
            <div className="p-2.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium">
              {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Repository Display Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. payment-gateway-service"
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Public Repository Path / URL
            </label>
            <input
              type="text"
              value={pathWithNamespace}
              onChange={(e) => setPathWithNamespace(e.target.value)}
              placeholder="e.g. owner/repo-name or https://github.com/owner/repo"
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Default Branch Name
            </label>
            <input
              type="text"
              value={defaultBranch}
              onChange={(e) => setDefaultBranch(e.target.value)}
              placeholder="main"
              className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900 font-mono"
            />
          </div>

          {/* Footer controls */}
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
              {loading ? 'Registering...' : '+ Register Repository'}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
