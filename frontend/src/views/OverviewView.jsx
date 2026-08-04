import React from 'react';
import { 
  GitPullRequest, 
  ShieldAlert, 
  Clock, 
  Zap, 
  ArrowUpRight, 
  ShieldCheck,
  Boxes
} from 'lucide-react';

export function OverviewView({ data, onSelectTab, onSelectReview }) {
  const { overview = {}, reviews = [], repositories = [] } = data;

  const totalRevs = overview.total_reviews ?? reviews.length;
  const criticalFound = overview.critical_issues_found ?? 0;
  const criticalFixed = overview.critical_issues_fixed ?? 0;
  const resolutionRate = criticalFound > 0 ? ((criticalFixed / criticalFound) * 100).toFixed(1) + '%' : '100%';

  const statCards = [
    {
      title: 'Total Code Reviews',
      value: totalRevs.toLocaleString(),
      change: totalRevs > 0 ? '+100%' : '0%',
      period: 'total completed',
      icon: GitPullRequest,
    },
    {
      title: 'Critical Issues Resolved',
      value: `${criticalFixed} / ${criticalFound}`,
      change: resolutionRate,
      period: 'resolution rate',
      icon: ShieldAlert,
    },
    {
      title: 'Avg Scan Time',
      value: `${overview.avg_review_time_seconds ?? 0}s`,
      change: 'turnaround',
      period: 'per review',
      icon: Clock,
    },
    {
      title: 'Engineering Hours Saved',
      value: `${overview.time_saved_hours ?? 0} hrs`,
      change: 'automated',
      period: 'reviews',
      icon: Zap,
    }
  ];

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            System Overview & Analytics
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated code review metrics, pull request throughput, and security health across active projects.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            Accuracy: {overview.ai_accuracy_rate ?? 100}%
          </span>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="p-4 rounded-lg bg-white border border-slate-200 shadow-sm space-y-2"
            >
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-xs font-medium">{card.title}</span>
                <Icon className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-bold text-slate-900 tracking-tight">
                {card.value}
              </div>
              <div className="text-[11px] text-slate-500 flex items-center gap-1">
                <span className="font-semibold text-emerald-600">{card.change}</span>
                <span>• {card.period}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Content Grid: Recent Scans & Repository List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Recent Code Reviews */}
        <div className="lg:col-span-2 rounded-lg bg-white border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Recent Pull Request Scans
            </h3>
            <button
              onClick={() => onSelectTab('reviews')}
              className="text-xs font-medium text-slate-600 hover:text-slate-900 flex items-center gap-1"
            >
              View all <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>

          <div className="divide-y divide-slate-100">
            {reviews.length === 0 ? (
              <div className="py-8 text-center text-slate-400 text-xs">
                No code review scans recorded yet. Trigger a pull request scan or connect a repository.
              </div>
            ) : (
              reviews.slice(0, 4).map((review) => (
                <div
                  key={review.id}
                  onClick={() => onSelectReview(review)}
                  className="py-3 first:pt-0 last:pb-0 flex items-center justify-between gap-4 cursor-pointer hover:bg-slate-50 p-2 rounded transition-colors"
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <img
                      src={review.author_avatar}
                      alt={review.author}
                      className="w-7 h-7 rounded-full border border-slate-200 object-cover shrink-0 mt-0.5"
                    />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-semibold text-slate-400">
                          #{review.pr_number}
                        </span>
                        <h4 className="text-xs font-semibold text-slate-900 truncate hover:text-sky-600">
                          {review.title}
                        </h4>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        <span className="font-mono text-slate-700">{review.repository}</span> • by {review.author} • {review.time_taken}
                      </div>
                    </div>
                  </div>

                  <div className="shrink-0">
                    {review.status === 'APPROVED' && (
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Approved
                      </span>
                    )}
                    {review.status === 'APPROVED_WITH_COMMENTS' && (
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-sky-50 text-sky-700 border border-sky-200">
                        Comments Added
                      </span>
                    )}
                    {review.status === 'NEEDS_REVISION' && (
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-rose-50 text-rose-700 border border-rose-200">
                        Needs Revision
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Repositories Quick Overview */}
        <div className="rounded-lg bg-white border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Monitored Repositories
            </h3>
            <button
              onClick={() => onSelectTab('repositories')}
              className="text-xs font-medium text-slate-600 hover:text-slate-900"
            >
              Manage
            </button>
          </div>

          <div className="space-y-2.5">
            {repositories.length === 0 ? (
              <div className="py-8 text-center text-slate-400 text-xs">
                No repositories registered yet.
              </div>
            ) : (
              repositories.map((repo) => (
                <div
                  key={repo.id}
                  className="p-3 rounded bg-slate-50 border border-slate-100 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-bold text-slate-900">{repo.name}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      {repo.language} • {repo.coverage} coverage
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-emerald-600">{repo.health_score}%</span>
                    <div className="text-[10px] text-slate-400">{repo.open_prs} open PRs</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
