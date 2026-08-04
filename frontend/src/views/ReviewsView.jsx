import React, { useState } from 'react';
import { 
  GitPullRequest, 
  User, 
  Clock, 
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  XCircle
} from 'lucide-react';

export function ReviewsView({ reviews = [], onSelectReview, searchQuery = '' }) {
  const [statusFilter, setStatusFilter] = useState('ALL');

  const filteredReviews = reviews.filter((r) => {
    const matchesSearch = 
      r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.repository.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.pr_number.toString().includes(searchQuery);

    const matchesStatus = 
      statusFilter === 'ALL' || r.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            Pull Request Code Reviews
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated code security analysis, diff inspection, and line-by-line feedback.
          </p>
        </div>

        {/* Filter Buttons */}
        <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-md text-xs">
          {[
            { id: 'ALL', label: 'All' },
            { id: 'APPROVED', label: 'Approved' },
            { id: 'APPROVED_WITH_COMMENTS', label: 'Comments' },
            { id: 'NEEDS_REVISION', label: 'Needs Revision' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                statusFilter === tab.id
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Reviews List */}
      <div className="rounded-lg bg-white border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
        {filteredReviews.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <GitPullRequest className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-medium">No code reviews match your current filters.</p>
          </div>
        ) : (
          filteredReviews.map((review) => (
            <div
              key={review.id}
              onClick={() => onSelectReview(review)}
              className="p-4 hover:bg-slate-50 transition-colors cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                    #{review.pr_number}
                  </span>
                  <h3 className="text-sm font-bold text-slate-900 hover:text-sky-600 truncate">
                    {review.title}
                  </h3>
                </div>

                <p className="text-xs text-slate-600 line-clamp-1">
                  {review.summary}
                </p>

                <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
                  <span className="font-mono font-semibold text-slate-700">
                    {review.repository}
                  </span>
                  <span>•</span>
                  <span>by {review.author}</span>
                  <span>•</span>
                  <span>{review.time_taken}</span>
                  <span>•</span>
                  <span className="font-mono text-emerald-600">+{review.lines_added}</span>
                  <span className="font-mono text-rose-600">-{review.lines_deleted}</span>
                </div>
              </div>

              {/* Status and Severity Badges */}
              <div className="flex items-center gap-3 shrink-0 justify-between md:justify-end">
                <div className="flex items-center gap-1 text-[11px]">
                  {review.findings_count.critical > 0 && (
                    <span className="px-2 py-0.5 rounded font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      {review.findings_count.critical} Critical
                    </span>
                  )}
                  {review.findings_count.high > 0 && (
                    <span className="px-2 py-0.5 rounded font-bold bg-amber-50 text-amber-700 border border-amber-200">
                      {review.findings_count.high} High
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5">
                  {review.status === 'APPROVED' && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Approved
                    </span>
                  )}
                  {review.status === 'APPROVED_WITH_COMMENTS' && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded bg-sky-50 text-sky-700 border border-sky-200">
                      <AlertTriangle className="w-3.5 h-3.5" /> Comments
                    </span>
                  )}
                  {review.status === 'NEEDS_REVISION' && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded bg-rose-50 text-rose-700 border border-rose-200">
                      <XCircle className="w-3.5 h-3.5" /> Revision
                    </span>
                  )}
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
