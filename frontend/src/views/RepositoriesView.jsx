import React, { useState } from 'react';
import { 
  Boxes, 
  GitBranch, 
  ExternalLink,
  Code,
  ShieldCheck,
  Plus,
  Lock
} from 'lucide-react';
import { AddRepositoryModal } from '../components/modals/AddRepositoryModal';

export function RepositoriesView({ repositories = [], onRepositoryAdded, currentUser }) {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const isAdmin = currentUser?.role === 'ADMIN';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            Repository Health & Monitoring
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Overview of code coverage, active security scans, and connected Git repositories.
          </p>
        </div>

        {isAdmin ? (
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-slate-900 rounded-md hover:bg-slate-800 transition-colors shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Connect Public Repository</span>
          </button>
        ) : (
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-500 bg-slate-100 border border-slate-200 rounded-md">
            <Lock className="w-3.5 h-3.5 text-slate-400" />
            <span>Only Admin Can Connect Repositories</span>
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {repositories.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-white rounded-lg border border-slate-200 col-span-full">
            <Boxes className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-medium">No repositories registered yet.</p>
            <p className="text-xs text-slate-400 mt-1">Click "Connect Public Repository" above to register your GitHub repository for automated AI code reviews.</p>
          </div>
        ) : (
          repositories.map((repo) => (
            <div
              key={repo.id}
              className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <Boxes className="w-4 h-4 text-slate-700" />
                      <h3 className="text-sm font-bold text-slate-900">
                        {repo.name}
                      </h3>
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-500">
                      <span className="flex items-center gap-1 font-mono">
                        <GitBranch className="w-3 h-3 text-slate-400" />
                        {repo.branch || 'main'}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Code className="w-3 h-3 text-slate-400" />
                        {repo.language || 'Git Repo'}
                      </span>
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
                    {repo.health_score ?? 100}% Health
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 mt-4 p-3 rounded bg-slate-50 border border-slate-100 text-center">
                  <div>
                    <div className="text-[10px] text-slate-400">Open PRs</div>
                    <div className="text-xs font-bold text-slate-900">{repo.open_prs || 0}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">Findings</div>
                    <div className="text-xs font-bold text-slate-900">{repo.total_findings || 0}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">Status</div>
                    <div className="text-xs font-bold text-emerald-600">{repo.coverage || 'Active'}</div>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <div className="flex items-center gap-1 text-slate-500 text-[11px]">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Public Repository Monitored</span>
                </div>

                <a
                  href={repo.url || `https://github.com/${repo.path_with_namespace || repo.name}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 font-medium transition-colors"
                >
                  GitHub Repo <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add Repository Modal (Admin Only) */}
      {isAdmin && (
        <AddRepositoryModal
          isOpen={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
          onRepositoryAdded={(newRepo) => {
            if (onRepositoryAdded) onRepositoryAdded(newRepo);
          }}
        />
      )}
    </div>
  );
}
