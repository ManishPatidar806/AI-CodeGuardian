import React from 'react';
import { 
  Shield, 
  GitPullRequest, 
  Boxes, 
  Trophy, 
  Bug, 
  Sliders, 
  Lock, 
  LogIn, 
  ArrowRight, 
  CheckCircle2, 
  ShieldAlert, 
  Wand2, 
  Code, 
  GitBranch,
  ExternalLink,
  ChevronRight
} from 'lucide-react';

export function LandingPage({ onOpenAuthModal }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased flex flex-col">
      {/* Top Header Bar */}
      <header className="h-16 border-b border-slate-200 bg-white sticky top-0 z-50 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-slate-900 text-white flex items-center justify-center font-bold shadow-xs">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900 tracking-tight">
              AI CodeGuardian
            </h1>
            <span className="text-[10px] text-slate-400 font-mono">
              Self-Hosted Open Source v2.5
            </span>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-slate-600">
          <a href="#features" className="hover:text-slate-900 transition-colors">Features</a>
          <a href="#architecture" className="hover:text-slate-900 transition-colors">Architecture</a>
          <a href="#workflow" className="hover:text-slate-900 transition-colors">Workflow</a>
          <a href="#security" className="hover:text-slate-900 transition-colors">Security</a>
        </nav>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenAuthModal}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-slate-900 rounded-md hover:bg-slate-800 transition-colors shadow-sm cursor-pointer"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In / Launch App</span>
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-16 pb-14 px-6 bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700">
            <Shield className="w-3.5 h-3.5 text-slate-900" />
            <span>Autonomous Pull Request Security & Quality Inspection</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 leading-tight">
            Automated Code Review System <br />
            <span className="text-slate-600 font-bold">For Software Development Teams</span>
          </h1>

          <p className="max-w-2xl mx-auto text-xs sm:text-sm text-slate-600 leading-relaxed">
            AI CodeGuardian integrates with your GitHub & GitLab repositories to perform automated code reviews, detect OWASP security flaws, enforce architectural standards, and generate 1-click code fixes.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={onOpenAuthModal}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 text-xs font-bold text-white bg-slate-900 rounded-md hover:bg-slate-800 transition-colors shadow-sm cursor-pointer"
            >
              <span>Access Application Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <a
              href="#workflow"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-md hover:bg-slate-50 transition-colors"
            >
              <span>View System Workflow</span>
            </a>
          </div>
        </div>

        {/* Live Interface Mockup Card */}
        <div className="max-w-4xl mx-auto mt-12 rounded-lg bg-white border border-slate-200 shadow-sm overflow-hidden text-xs">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2 font-mono text-[11px] font-semibold text-slate-700">
              <GitPullRequest className="w-4 h-4 text-slate-700" />
              <span>Pull Request Scan #104</span>
              <span className="text-slate-400">•</span>
              <span className="text-slate-500">main branch</span>
            </div>
            <span className="px-2.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
              Grade A+ (98.4% Health Score)
            </span>
          </div>

          <div className="p-5 space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded bg-slate-50 border border-slate-100 font-mono text-[11px]">
              <div>
                <div className="text-[10px] text-slate-400">Repository</div>
                <div className="font-bold text-slate-900">company/auth-service</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400">Author</div>
                <div className="font-semibold text-slate-900">staff_engineer</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400">Scan Latency</div>
                <div className="font-semibold text-slate-900">12.4s</div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400">Lines Changed</div>
                <div className="font-semibold text-emerald-600">+120 / -45</div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="font-bold text-slate-900 text-xs flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                    CRITICAL
                  </span>
                  <span>SQL Injection Vulnerability Prevented</span>
                </div>
                <span className="font-mono text-[10px] text-slate-400">app/db/query.py:12</span>
              </div>

              <div className="p-3.5 rounded bg-slate-900 text-slate-100 font-mono text-[11px]">
                <div className="text-rose-400 mb-1">{'- query = f"SELECT * FROM users WHERE email=\'{user_email}\'"'}</div>
                <div className="text-emerald-400">{'+ stmt = select(UserModel).where(UserModel.email == user_email)'}</div>
              </div>
            </div>

            <div className="p-3 rounded bg-slate-50 border border-slate-200 text-slate-700 text-xs leading-relaxed">
              <span className="font-bold text-slate-900">Suggested Fix: </span>
              Replaced raw string interpolation with parameterized query binding to mitigate SQL Injection risks (CWE-89).
            </div>
          </div>
        </div>
      </section>

      {/* Core Technical Modules Grid */}
      <section id="features" className="py-14 px-6 max-w-7xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
            Enterprise System Capabilities
          </h2>
          <p className="text-xs text-slate-500 max-w-xl mx-auto">
            Comprehensive security inspection, code quality enforcement, and pull request workflow automation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-3">
            <div className="w-8 h-8 rounded bg-slate-100 text-slate-900 flex items-center justify-center">
              <GitPullRequest className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Automated PR Diff Inspection
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Intercept pull requests automatically via Webhooks, perform line-by-line static analysis, and post inline comments directly onto code diffs.
            </p>
          </div>

          <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-3">
            <div className="w-8 h-8 rounded bg-slate-100 text-slate-900 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              SAST & Secret Leak Scanner
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Scan commit diffs for OWASP Top 10 vulnerabilities, memory flaws, hardcoded RSA keys, API tokens, and credentials before merging.
            </p>
          </div>

          <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-3">
            <div className="w-8 h-8 rounded bg-slate-100 text-slate-900 flex items-center justify-center">
              <Wand2 className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              AI Code Fix Synthesizer
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Generate production-ready code remediation patches for flagged security findings with explanation notes and 1-click copy support.
            </p>
          </div>

          <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-3">
            <div className="w-8 h-8 rounded bg-slate-100 text-slate-900 flex items-center justify-center">
              <Trophy className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Developer Security Rankings
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Gamify clean code standards with developer scorecards, clean code pass rates, resolved issue metrics, and achievement badges.
            </p>
          </div>

          <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-3">
            <div className="w-8 h-8 rounded bg-slate-100 text-slate-900 flex items-center justify-center">
              <Sliders className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Admin Policy & Auto-Merge Engine
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Define custom auto-approve score thresholds, select strictness policies, and execute direct main-branch merges from the Web UI.
            </p>
          </div>

          <div className="p-5 rounded-lg bg-white border border-slate-200 shadow-sm space-y-3">
            <div className="w-8 h-8 rounded bg-slate-100 text-slate-900 flex items-center justify-center">
              <Lock className="w-4 h-4" />
            </div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Self-Hosted & Complete Data Control
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Deploy on your local server, Docker, or Kubernetes infrastructure with local SQLite/PostgreSQL storage and total code privacy.
            </p>
          </div>
        </div>
      </section>

      {/* System Workflow */}
      <section id="workflow" className="py-12 px-6 bg-white border-y border-slate-200">
        <div className="max-w-5xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-xl font-bold text-slate-900">
              System Execution Workflow
            </h2>
            <p className="text-xs text-slate-500">
              Three-step integration process from code commit to automated merge.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
              <div className="text-xs font-mono font-bold text-slate-400">STEP 01</div>
              <h3 className="text-sm font-bold text-slate-900">Connect Repository</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Register your GitHub/GitLab public or private repository namespace in the Admin Repositories panel.
              </p>
            </div>

            <div className="p-5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
              <div className="text-xs font-mono font-bold text-slate-400">STEP 02</div>
              <h3 className="text-sm font-bold text-slate-900">Webhook Interception</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Opening a Pull Request triggers the AI CodeGuardian inspection engine to analyze code diffs in real time.
              </p>
            </div>

            <div className="p-5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
              <div className="text-xs font-mono font-bold text-slate-400">STEP 03</div>
              <h3 className="text-sm font-bold text-slate-900">Inline Review & Auto-Merge</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Line-by-line feedback is posted back to Git, and compliant code meeting threshold rules is approved for merge.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 px-6 mt-auto text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-slate-900" />
            <span className="font-bold text-slate-900">AI CodeGuardian</span>
            <span>• Self-Hosted Edition</span>
          </div>

          <div className="flex items-center gap-4 text-[11px]">
            <button
              onClick={onOpenAuthModal}
              className="font-bold text-slate-900 hover:underline cursor-pointer"
            >
              Sign In to Instance
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
