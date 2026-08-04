import React, { useState } from 'react';
import { 
  X, 
  Wand2, 
  Check, 
  Copy, 
  ShieldCheck
} from 'lucide-react';
import { generateAIFixSuggestion } from '../../services/api';

export function FixGeneratorModal({ finding, onClose }) {
  const [loading, setLoading] = useState(false);
  const [fixResult, setFixResult] = useState(null);
  const [copied, setCopied] = useState(false);

  if (!finding) return null;

  const handleGenerate = async () => {
    setLoading(true);
    const res = await generateAIFixSuggestion(finding);
    setLoading(false);
    if (res.success) {
      setFixResult(res.data);
    }
  };

  const handleCopy = () => {
    const textToCopy = fixResult ? fixResult.fixed_code : finding.suggested_fix;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-lg shadow-xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-100">
        
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <Wand2 className="w-4 h-4 text-slate-700" />
            <h2 className="text-sm font-bold text-slate-900">
              AI Code Fix Generator
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
        <div className="p-5 space-y-4 text-xs">
          <div>
            <div className="flex items-center gap-2 font-bold text-slate-900">
              <span className="px-2 py-0.5 rounded text-[10px] bg-rose-50 text-rose-700 border border-rose-200">
                {finding.severity}
              </span>
              <span>{finding.title}</span>
            </div>
            <p className="text-slate-500 mt-1">
              Location: <span className="font-mono text-slate-700">{finding.file}:{finding.line}</span>
            </p>
          </div>

          {/* Original Code */}
          <div className="space-y-1">
            <div className="text-[11px] font-bold text-rose-600 uppercase tracking-wider">
              Flagged Code Snippet
            </div>
            <div className="p-3 rounded bg-slate-900 text-rose-300 font-mono text-[11px]">
              <code>{finding.code_snippet}</code>
            </div>
          </div>

          {/* AI Fix Section */}
          {!fixResult ? (
            <div className="pt-2">
              <button
                onClick={handleGenerate}
                disabled={loading}
                className="w-full py-2.5 px-4 rounded font-bold text-white bg-slate-900 hover:bg-slate-800 transition-colors flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
              >
                <Wand2 className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>{loading ? 'Generating Code Patch...' : 'Synthesize Fix Patch'}</span>
              </button>
            </div>
          ) : (
            <div className="space-y-3 pt-2">
              <div className="text-[11px] font-bold text-emerald-600 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" /> Suggested Remediation Patch
              </div>

              <div className="p-3 rounded bg-slate-900 text-emerald-300 font-mono text-[11px]">
                <code>{fixResult.fixed_code}</code>
              </div>

              <p className="text-slate-600 bg-slate-50 p-3 rounded border border-slate-100 text-xs">
                {fixResult.explanation}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-200 bg-slate-50 flex justify-between items-center">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900"
          >
            Cancel
          </button>

          {fixResult && (
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-emerald-600 rounded hover:bg-emerald-700 transition-colors shadow-sm"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied!' : 'Copy Code Patch'}</span>
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
