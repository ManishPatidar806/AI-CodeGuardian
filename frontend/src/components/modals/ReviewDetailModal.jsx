import React, { useState } from 'react';
import { 
  X, 
  CheckCircle2, 
  GitMerge,
  Lock,
  Check
} from 'lucide-react';

export function ReviewDetailModal({ review, onClose, currentUser }) {
  const [merged, setMerged] = useState(false);
  const isAdmin = currentUser?.role === 'ADMIN';

  if (!review) return null;

  const handleMerge = () => {
    setMerged(true);
    setTimeout(() => {
      setMerged(false);
      onClose();
    }, 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-100">
        
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-mono text-xs font-bold text-slate-500 bg-slate-200 px-2 py-0.5 rounded">
              #{review.pr_number}
            </span>
            <h2 className="text-sm font-bold text-slate-900 truncate">
              {review.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto space-y-5 flex-1 text-xs">
          
          {/* Metadata */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded bg-slate-50 border border-slate-100">
            <div>
              <div className="text-[10px] text-slate-400">Repository</div>
              <div className="font-mono font-bold text-slate-900">{review.repository}</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-400">Author</div>
              <div className="font-semibold text-slate-900">{review.author}</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-400">Scan Duration</div>
              <div className="font-semibold text-slate-900">{review.time_taken}</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-400">Lines Changed</div>
              <div className="font-mono font-semibold text-emerald-600">
                +{review.lines_added} / -{review.lines_deleted}
              </div>
            </div>
          </div>

          {/* AI Summary */}
          <div className="space-y-1.5">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Summary Analysis
            </h3>
            <p className="text-slate-600 leading-relaxed bg-slate-50 p-3 rounded border border-slate-100">
              {review.summary}
            </p>
          </div>

          {/* Git Diff */}
          {review.diff_snippet && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Git Diff
              </h3>
              <div className="p-3.5 rounded bg-slate-900 text-slate-100 font-mono text-[11px] overflow-x-auto">
                <pre className="whitespace-pre">{review.diff_snippet}</pre>
              </div>
            </div>
          )}

          {/* Findings */}
          <div className="space-y-2.5">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Line-by-Line Findings ({review.ai_comments?.length || 0})
            </h3>
            
            {review.ai_comments?.map((comment, cIdx) => (
              <div
                key={cIdx}
                className="p-3.5 rounded bg-white border border-slate-200 shadow-xs space-y-1.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                      comment.severity === 'CRITICAL' 
                        ? 'bg-rose-50 text-rose-700 border border-rose-200'
                        : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}>
                      {comment.severity}
                    </span>
                    <span className="font-bold text-slate-900">
                      {comment.title}
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-slate-400">
                    {comment.file}:{comment.line}
                  </span>
                </div>

                <p className="text-slate-600">
                  {comment.description}
                </p>

                <div className="p-2 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono text-[11px]">
                  <span className="font-bold">Suggested Fix: </span>
                  {comment.suggestion}
                </div>
              </div>
            ))}
          </div>

        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <div>
            {!isAdmin && (
              <span className="text-[11px] text-slate-500 flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-slate-400" />
                Only Admins can execute code merges to main branch.
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded hover:bg-slate-50 transition-colors"
            >
              Close
            </button>

            {isAdmin && (
              <button
                onClick={handleMerge}
                disabled={merged}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-slate-900 rounded hover:bg-slate-800 transition-colors shadow-sm disabled:opacity-50"
              >
                {merged ? <Check className="w-3.5 h-3.5" /> : <GitMerge className="w-3.5 h-3.5" />}
                <span>{merged ? 'Merged into Main!' : 'Admin Merge to Main Branch'}</span>
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
