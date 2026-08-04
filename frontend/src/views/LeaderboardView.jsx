import React from 'react';
import { Trophy } from 'lucide-react';

export function LeaderboardView({ leaderboard = [] }) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            Developer Security Rankings
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Recognizing engineers based on clean code scores, resolved security issues, and PR review pass rates.
          </p>
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-50 text-amber-800 border border-amber-200 text-xs font-medium rounded">
          <Trophy className="w-3.5 h-3.5 text-amber-600" />
          <span>{new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}</span>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="rounded-lg bg-white border border-slate-200 shadow-sm overflow-hidden">
        {leaderboard.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Trophy className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-medium">No developer activity recorded yet.</p>
            <p className="text-xs text-slate-400 mt-1">Developer rankings will update as pull request scans are processed.</p>
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-4 w-12 text-center">Rank</th>
                <th className="py-3 px-4">Engineer</th>
                <th className="py-3 px-4 text-center">Clean Code Score</th>
                <th className="py-3 px-4 text-center">Passed PRs</th>
                <th className="py-3 px-4 text-center">Critical Fixes</th>
                <th className="py-3 px-4">Badges</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {leaderboard.map((dev) => (
                <tr key={dev.rank} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3.5 px-4 text-center font-bold text-slate-500">
                    {dev.rank === 1 && '🥇'}
                    {dev.rank === 2 && '🥈'}
                    {dev.rank === 3 && '🥉'}
                    {dev.rank > 3 && `#${dev.rank}`}
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-3">
                      <img
                        src={dev.avatar}
                        alt={dev.name}
                        className="w-8 h-8 rounded-full border border-slate-200 object-cover"
                      />
                      <div>
                        <div className="font-bold text-slate-900 text-xs">
                          {dev.name}
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {dev.role}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {dev.clean_code_score}%
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-center font-mono font-bold text-slate-900">
                    {dev.reviews_passed}
                  </td>
                  <td className="py-3.5 px-4 text-center font-mono font-bold text-rose-600">
                    {dev.critical_fixes}
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex flex-wrap gap-1">
                      {dev.badges.map((badge, bIdx) => (
                        <span
                          key={bIdx}
                          className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 border border-slate-200"
                        >
                          {badge}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
