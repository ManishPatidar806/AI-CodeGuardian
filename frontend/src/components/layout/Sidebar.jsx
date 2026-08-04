import React from 'react';
import { 
  Shield, 
  LayoutDashboard, 
  GitPullRequest, 
  Boxes, 
  Trophy, 
  Bug, 
  Sliders,
  Users,
  User,
  Check,
  Lock
} from 'lucide-react';

export function Sidebar({ activeTab, onTabChange, currentUser }) {
  const isAdmin = currentUser?.role === 'ADMIN';

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard, public: true },
    { id: 'reviews', label: 'Code Reviews', icon: GitPullRequest, badge: '3', public: true },
    { id: 'repositories', label: 'Repositories', icon: Boxes, public: true },
    { id: 'leaderboard', label: 'Leaderboard', icon: Trophy, public: true },
    { id: 'findings', label: 'Findings', icon: Bug, badge: '4', public: true },
    { id: 'profile', label: 'My Profile', icon: User, public: true },
    { id: 'users', label: 'Employees', icon: Users, adminOnly: true },
    { id: 'config', label: 'Settings', icon: Sliders, adminOnly: true },
  ];

  return (
    <aside className="w-60 border-r border-slate-200 bg-white flex flex-col justify-between h-screen sticky top-0 z-40">
      <div>
        {/* Brand Logo */}
        <div className="h-16 px-5 flex items-center gap-2.5 border-b border-slate-100">
          <div className="w-7 h-7 rounded bg-slate-900 text-white flex items-center justify-center font-bold">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-900 tracking-tight">
              AI CodeGuardian
            </h1>
            <span className="text-[10px] text-slate-400 font-mono">
              Self-Hosted Open Source
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            const isRestricted = item.adminOnly && !isAdmin;

            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                disabled={isRestricted}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  isRestricted
                    ? 'opacity-40 cursor-not-allowed text-slate-400'
                    : isActive
                    ? 'bg-slate-100 text-slate-900 font-semibold'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
                title={isRestricted ? 'Admin Access Only' : ''}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-slate-900' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>

                {isRestricted ? (
                  <Lock className="w-3 h-3 text-slate-400" />
                ) : item.adminOnly ? (
                  <span className="px-1.5 py-0.2 text-[9px] font-bold rounded bg-slate-900 text-white">
                    ADMIN
                  </span>
                ) : item.badge ? (
                  <span className={`px-1.5 py-0.2 text-[10px] font-semibold rounded ${
                    isActive ? 'bg-slate-200 text-slate-800' : 'bg-slate-100 text-slate-500'
                  }`}>
                    {item.badge}
                  </span>
                ) : null}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Status */}
      <div className="p-3 border-t border-slate-100">
        <div className="p-2.5 rounded-md bg-slate-50 border border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 inline-block"></span>
            <span className="text-xs font-medium text-slate-700">
              Self-Hosted Instance
            </span>
          </div>
          <Check className="w-3.5 h-3.5 text-emerald-600" />
        </div>
      </div>
    </aside>
  );
}
