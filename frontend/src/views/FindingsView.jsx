import React, { useState } from 'react';
import { 
  Bug, 
  Wand2
} from 'lucide-react';

export function FindingsView({ findings = [], onGenerateFix, searchQuery = '' }) {
  const [severityFilter, setSeverityFilter] = useState('ALL');

  const filteredFindings = findings.filter((f) => {
    const matchesSearch =
      f.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.file.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.repository.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.category.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSeverity = 
      severityFilter === 'ALL' || f.severity === severityFilter;

    return matchesSearch && matchesSeverity;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            Security & Quality Findings
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Active code vulnerabilities, OWASP patterns, and concurrency issues requiring remediation.
          </p>
        </div>

        {/* Severity Filter Tabs */}
        <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-md text-xs">
          {[
            { id: 'ALL', label: 'All' },
            { id: 'CRITICAL', label: 'Critical' },
            { id: 'HIGH', label: 'High' },
            { id: 'MEDIUM', label: 'Medium' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSeverityFilter(tab.id)}
              className={`px-2 py-1 rounded font-medium transition-colors ${
                severityFilter === tab.id
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-4">
        {filteredFindings.length === 0 ? (
          <div className="p-12 bg-white rounded-lg border border-slate-200 text-center text-slate-500">
            <Bug className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-medium">No findings match your search parameters.</p>
          </div>
        ) : (
          filteredFindings.map((finding) => (
            <div
              key={finding.id}
              className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start gap-2.5 min-w-0">
                  {finding.severity === 'CRITICAL' && (
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200 shrink-0">
                      CRITICAL
                    </span>
                  )}
                  {finding.severity === 'HIGH' && (
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200 shrink-0">
                      HIGH
                    </span>
                  )}
                  {finding.severity === 'MEDIUM' && (
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-sky-50 text-sky-700 border border-sky-200 shrink-0">
                      MEDIUM
                    </span>
                  )}
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">
                      {finding.title}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                      <span className="font-semibold text-slate-700">
                        {finding.category}
                      </span>
                      <span>•</span>
                      <span className="font-mono">
                        {finding.repository} ({finding.file}:{finding.line})
                      </span>
                      <span>•</span>
                      <span>{finding.detected_date}</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => onGenerateFix(finding)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-slate-900 rounded-md hover:bg-slate-800 transition-colors shrink-0 shadow-sm"
                >
                  <Wand2 className="w-3.5 h-3.5" />
                  <span>Generate Fix</span>
                </button>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                {finding.description}
              </p>

              <div className="p-3 rounded bg-slate-900 text-slate-100 font-mono text-[11px] overflow-x-auto">
                <code>{finding.code_snippet}</code>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
