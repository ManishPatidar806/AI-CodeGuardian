import React, { useState } from 'react';
import { 
  Check, 
  Save, 
  Cpu,
  Lock
} from 'lucide-react';

export function ConfigView({ config = {}, onSaveConfig, currentUser }) {
  const isAdmin = currentUser?.role === 'ADMIN';

  const [formData, setFormData] = useState({
    review_mode: config.review_mode || 'STRICT',
    auto_approve_score: config.auto_approve_score || 90,
    enable_sast_scan: config.enable_sast_scan !== false,
    enable_secret_scanner: config.enable_secret_scanner !== false,
    enable_dependency_audit: config.enable_dependency_audit !== false,
    ai_model_name: config.ai_model_name || 'Gemini 2.5 Pro (Security Edition)',
  });

  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isAdmin) return;
    onSaveConfig(formData);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  if (!isAdmin) {
    return (
      <div className="p-12 text-center bg-white rounded-lg border border-slate-200 shadow-sm space-y-3">
        <Lock className="w-10 h-10 mx-auto text-rose-500" />
        <h2 className="text-base font-bold text-slate-900">Admin Authorization Required</h2>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          System settings, AI model selection, review strictness policies, and security scanner toggles can only be modified by the System Administrator.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">
              Guardian AI Settings
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-white">
              ADMIN PANEL
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure automated code review policies, security scanner engines, and approval thresholds.
          </p>
        </div>

        {savedSuccess && (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <Check className="w-3.5 h-3.5" /> Settings Saved
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: AI Engine & Policy */}
        <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Cpu className="w-4 h-4 text-slate-700" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              AI Analysis Engine
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Selected AI Model
              </label>
              <select
                value={formData.ai_model_name}
                onChange={(e) => setFormData({ ...formData, ai_model_name: e.target.value })}
                className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
              >
                <option value="Gemini 2.5 Pro (Security Edition)">Gemini 2.5 Pro (Security Edition)</option>
                <option value="Gemini 2.5 Flash (Ultra Fast)">Gemini 2.5 Flash (Ultra Fast)</option>
                <option value="Claude 3.5 Sonnet (Extended Context)">Claude 3.5 Sonnet (Extended Context)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Review Policy Rigor
              </label>
              <select
                value={formData.review_mode}
                onChange={(e) => setFormData({ ...formData, review_mode: e.target.value })}
                className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md text-slate-900 focus:outline-none focus:ring-1 focus:ring-slate-900"
              >
                <option value="STRICT">Strict (Block PR on Medium+ flaws)</option>
                <option value="BALANCED">Balanced (Block only High/Critical)</option>
                <option value="ADVISORY">Advisory (Comments only, non-blocking)</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs font-medium text-slate-700 mb-1">
              <span>Auto-Approve Threshold Score ({formData.auto_approve_score}%)</span>
              <span className="text-slate-400">Default: 90%</span>
            </div>
            <input
              type="range"
              min="70"
              max="100"
              value={formData.auto_approve_score}
              onChange={(e) => setFormData({ ...formData, auto_approve_score: Number(e.target.value) })}
              className="w-full h-1.5 bg-slate-200 rounded-md appearance-none cursor-pointer accent-slate-900"
            />
          </div>
        </div>

        {/* Section 2: Active Security Checkers */}
        <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Lock className="w-4 h-4 text-slate-700" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Security Inspection Engines
            </h3>
          </div>

          <div className="space-y-2.5">
            {[
              { key: 'enable_sast_scan', label: 'SAST Vulnerability & Quality Scanner', desc: 'Checks pull requests against OWASP Top 10 and memory safety rules.' },
              { key: 'enable_secret_scanner', label: 'Hardcoded Secret & Key Scanner', desc: 'Detects accidental API key leaks, RSA keys, and secret tokens.' },
              { key: 'enable_dependency_audit', label: 'Dependency Vulnerability Audit', desc: 'Scans package updates for known CVE security advisories.' },
            ].map((item) => (
              <div key={item.key} className="flex items-start justify-between p-3 rounded bg-slate-50 border border-slate-100">
                <div>
                  <div className="text-xs font-semibold text-slate-900">{item.label}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">{item.desc}</div>
                </div>
                <input
                  type="checkbox"
                  checked={formData[item.key]}
                  onChange={(e) => setFormData({ ...formData, [item.key]: e.target.checked })}
                  className="w-4 h-4 rounded border-slate-300 text-slate-900 focus:ring-slate-900 cursor-pointer mt-0.5"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button
            type="submit"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-slate-900 rounded-md hover:bg-slate-800 transition-colors shadow-sm"
          >
            <Save className="w-3.5 h-3.5" /> Save Settings
          </button>
        </div>
      </form>
    </div>
  );
}
