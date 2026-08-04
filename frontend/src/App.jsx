import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { OverviewView } from './views/OverviewView';
import { ReviewsView } from './views/ReviewsView';
import { RepositoriesView } from './views/RepositoriesView';
import { LeaderboardView } from './views/LeaderboardView';
import { FindingsView } from './views/FindingsView';
import { ConfigView } from './views/ConfigView';
import { UserManagementView } from './views/UserManagementView';
import { ProfileView } from './views/ProfileView';
import { ReviewDetailModal } from './components/modals/ReviewDetailModal';
import { FixGeneratorModal } from './components/modals/FixGeneratorModal';
import { AuthModal } from './components/modals/AuthModal';
import { LoginPage } from './views/LoginPage';
import { 
  fetchDashboardOverview, 
  updateConfigData 
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedRepo, setSelectedRepo] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Multi-user Profile Session (stored in localStorage, null by default)
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('codeguardian_user');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  const handleSetUser = (user) => {
    setCurrentUser(user);
    if (user) {
      localStorage.setItem('codeguardian_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('codeguardian_user');
    }
  };

  const [dashboardData, setDashboardData] = useState({
    overview: {},
    reviews: [],
    repositories: [],
    leaderboard: [],
    findings: [],
    config: {}
  });

  const [selectedReviewModal, setSelectedReviewModal] = useState(null);
  const [selectedFindingModal, setSelectedFindingModal] = useState(null);

  // Load Data
  const loadData = async (repoId = selectedRepo) => {
    setIsRefreshing(true);
    const res = await fetchDashboardOverview(repoId);
    if (res.success) {
      setDashboardData(res.data);
    }
    setIsRefreshing(false);
  };

  useEffect(() => {
    if (currentUser) {
      loadData(selectedRepo);
    }
  }, [selectedRepo, currentUser]);

  const handleSaveConfig = async (newConfig) => {
    const res = await updateConfigData(newConfig);
    if (res.success) {
      setDashboardData(prev => ({ ...prev, config: res.data }));
    }
  };

  const handleGenerateFixForFinding = (finding) => {
    setSelectedFindingModal(finding);
  };

  const handleRepositoryAdded = (newRepo) => {
    setDashboardData(prev => ({
      ...prev,
      repositories: [
        ...prev.repositories,
        {
          id: newRepo.id || `repo-${Date.now()}`,
          name: newRepo.name,
          path_with_namespace: newRepo.path_with_namespace,
          url: `https://github.com/${newRepo.path_with_namespace || newRepo.name}`,
          branch: newRepo.default_branch || 'main',
          language: 'Python / TypeScript',
          health_score: 100,
          open_prs: 0,
          total_findings: 0,
          coverage: '100%'
        }
      ]
    }));
  };

  // Render Combined Landing & Login Portal if User is not logged in
  if (!currentUser) {
    return <LoginPage onSelectUser={(profile) => handleSetUser(profile)} />;
  }

  return (
    <div className="min-h-screen flex bg-slate-50 text-slate-900 antialiased font-sans">
      {/* Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        currentUser={currentUser}
      />

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          repositories={dashboardData.repositories || []}
          selectedRepo={selectedRepo}
          onSelectRepo={setSelectedRepo}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onRefresh={() => loadData(selectedRepo)}
          isRefreshing={isRefreshing}
          currentUser={currentUser}
          onOpenAuthModal={() => setIsAuthModalOpen(true)}
          onLogout={() => handleSetUser(null)}
          onNavigateTab={setActiveTab}
        />

        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          <div className="max-w-7xl mx-auto space-y-6">
            {activeTab === 'overview' && (
              <OverviewView
                data={dashboardData}
                onSelectTab={setActiveTab}
                onSelectReview={setSelectedReviewModal}
              />
            )}

            {activeTab === 'reviews' && (
              <ReviewsView
                reviews={dashboardData.reviews || []}
                onSelectReview={setSelectedReviewModal}
                searchQuery={searchQuery}
              />
            )}

            {activeTab === 'repositories' && (
              <RepositoriesView
                repositories={dashboardData.repositories || []}
                onRepositoryAdded={handleRepositoryAdded}
                currentUser={currentUser}
              />
            )}

            {activeTab === 'leaderboard' && (
              <LeaderboardView
                leaderboard={dashboardData.leaderboard || []}
              />
            )}

            {activeTab === 'findings' && (
              <FindingsView
                findings={dashboardData.findings || []}
                onGenerateFix={handleGenerateFixForFinding}
                searchQuery={searchQuery}
              />
            )}

            {activeTab === 'profile' && (
              <ProfileView
                currentUser={currentUser}
                onUpdateUser={(updated) => handleSetUser(updated)}
              />
            )}

            {activeTab === 'users' && (
              <UserManagementView
                currentUser={currentUser}
              />
            )}

            {activeTab === 'config' && (
              <ConfigView
                config={dashboardData.config || {}}
                onSaveConfig={handleSaveConfig}
                currentUser={currentUser}
              />
            )}
          </div>
        </main>
      </div>

      {/* Modals */}
      <ReviewDetailModal
        review={selectedReviewModal}
        onClose={() => setSelectedReviewModal(null)}
        currentUser={currentUser}
      />

      <FixGeneratorModal
        finding={selectedFindingModal}
        onClose={() => setSelectedFindingModal(null)}
      />

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        currentUser={currentUser}
        onSelectUser={(profile) => handleSetUser(profile)}
      />
    </div>
  );
}
