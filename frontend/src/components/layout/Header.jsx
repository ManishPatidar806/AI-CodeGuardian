import React, { useState } from 'react';
import { 
  Search, 
  RotateCw, 
  ChevronDown, 
  FolderGit2,
  LogOut,
  User,
  Shield
} from 'lucide-react';

export function Header({ 
  repositories = [], 
  selectedRepo, 
  onSelectRepo, 
  searchQuery, 
  onSearchChange, 
  onRefresh, 
  isRefreshing,
  currentUser,
  onOpenAuthModal,
  onLogout,
  onNavigateTab
}) {
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  return (
    <header className="h-16 border-b border-slate-200 bg-white sticky top-0 z-30 px-6 flex items-center justify-between">
      {/* Search Input */}
      <div className="flex items-center gap-3 w-full max-w-md">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search pull requests, repositories, findings..."
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-900 focus:bg-white transition-all"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {/* Repository Dropdown */}
        <div className="relative flex items-center">
          <FolderGit2 className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
          <select
            value={selectedRepo}
            onChange={(e) => onSelectRepo(e.target.value)}
            className="pl-8 pr-7 py-1.5 text-xs font-medium bg-slate-50 border border-slate-200 rounded-md text-slate-700 hover:bg-slate-100 focus:outline-none focus:ring-1 focus:ring-slate-900 cursor-pointer appearance-none"
          >
            <option value="all">All Repositories</option>
            {repositories.map((repo) => (
              <option key={repo.id} value={repo.id}>
                {repo.name}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-50"
        >
          <RotateCw className={`w-3.5 h-3.5 text-slate-500 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>

        <div className="h-5 w-px bg-slate-200 mx-1" />

        {/* User Info & Profile Menu */}
        <div className="relative">
          {currentUser ? (
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="flex items-center gap-2 p-1 rounded-md hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <img
                src={currentUser.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=0f172a&color=fff`}
                alt={currentUser.name}
                className="w-7 h-7 rounded-full border border-slate-200 object-cover"
              />
              <div className="hidden sm:block text-left">
                <div className="text-xs font-medium text-slate-900 leading-tight">
                  {currentUser.name}
                </div>
                <div className="text-[10px] text-slate-500">
                  {currentUser.role}
                </div>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>
          ) : (
            <button
              onClick={onOpenAuthModal}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-slate-900 rounded-md hover:bg-slate-800 transition-colors"
            >
              <User className="w-3.5 h-3.5" />
              <span>Log In</span>
            </button>
          )}

          {/* Profile Dropdown Popup */}
          {showProfileMenu && currentUser && (
            <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-md shadow-lg py-1 z-50 text-xs">
              <div className="px-3 py-2 border-b border-slate-100">
                <div className="font-bold text-slate-900">{currentUser.name}</div>
                <div className="text-[10px] text-slate-400">{currentUser.email}</div>
              </div>

              <button
                onClick={() => {
                  setShowProfileMenu(false);
                  if (onNavigateTab) onNavigateTab('profile');
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2 text-slate-700 font-medium"
              >
                <User className="w-3.5 h-3.5 text-slate-500" />
                <span>My Profile & Settings</span>
              </button>

              <button
                onClick={() => {
                  setShowProfileMenu(false);
                  onOpenAuthModal();
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2 text-slate-700"
              >
                <Shield className="w-3.5 h-3.5 text-slate-400" />
                <span>Switch Profile</span>
              </button>

              <button
                onClick={() => {
                  setShowProfileMenu(false);
                  onLogout();
                }}
                className="w-full text-left px-3 py-2 hover:bg-slate-50 flex items-center gap-2 text-rose-600 border-t border-slate-100"
              >
                <LogOut className="w-3.5 h-3.5 text-rose-500" />
                <span>Log Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
