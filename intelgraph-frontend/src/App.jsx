import React, { useState, useEffect } from 'react';
import Sidebar from './components/layout/Sidebar';
import Topbar from './components/layout/Topbar';
import SafetyDisclaimer from './components/layout/SafetyDisclaimer';
import OverviewView from './components/dashboard/OverviewView';
import AssetDirectory from './components/assets/AssetDirectory';
import AssetProfile from './components/assets/AssetProfile';
import ActionCenterView from './components/actions/ActionCenterView';
import KnowledgeView from './components/knowledge/KnowledgeView';
import ComplianceView from './components/compliance/ComplianceView';
import ReportsView from './components/reports/ReportsView';
import AdminConsoleView from './components/admin/AdminConsoleView';
import NewAssetModal from './components/wizards/NewAssetModal';
import OnboardingWizardModal from './components/wizards/OnboardingWizardModal';
import DocumentViewerModal from './components/documents/DocumentViewerModal';
import GlobalSearchModal from './components/search/GlobalSearchModal';
import GlobalChatModal from './components/chat/GlobalChatModal';
import EnterpriseLoginModal from './components/auth/EnterpriseLoginModal';
import { api } from './services/api';

export default function App() {
  const [activeNav, setActiveNav] = useState('overview');
  const [selectedAssetTag, setSelectedAssetTag] = useState(null);
  
  // Enterprise Authentication State
  const [currentUser, setCurrentUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [tenantInfo, setTenantInfo] = useState(null);
  const [isImpersonating, setIsImpersonating] = useState(false);
  const [impersonationInfo, setImpersonationInfo] = useState(null);

  // Overview data
  const [overviewData, setOverviewData] = useState(null);

  // Modals & Navigation
  const [searchOpen, setSearchOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [newAssetModalOpen, setNewAssetModalOpen] = useState(false);
  const [onboardingModalOpen, setOnboardingModalOpen] = useState(false);
  const [docViewerId, setDocViewerId] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Initial Enterprise Session Load
  const initSession = async () => {
    const savedToken = localStorage.getItem('intelgraph_token');
    try {
      const res = await api.getMe(savedToken);
      if (res && res.user) {
        setCurrentUser(res.user);
        setAuthToken(res.token);
        setTenantInfo({
          tenant_id: res.tenant_id,
          name: res.organization_name,
          industry: res.industry
        });
        setIsImpersonating(res.is_impersonating || false);
        setImpersonationInfo(res.impersonation_info || null);
        loadOverview(res.user.role);
      }
    } catch (e) {
      console.warn('Initial session restore failed, fetching platform baseline:', e);
      try {
        const fallback = await api.getMe();
        if (fallback && fallback.user) {
          setCurrentUser(fallback.user);
          setAuthToken(fallback.token);
          setTenantInfo({
            tenant_id: fallback.tenant_id,
            name: fallback.organization_name,
            industry: fallback.industry
          });
          loadOverview(fallback.user.role);
        }
      } catch (err) {
        console.error('Failed to load fallback session:', err);
      }
    }
  };

  useEffect(() => {
    initSession();
  }, []);

  const loadOverview = async (role = currentUser?.role || 'Maintenance Engineer') => {
    try {
      const data = await api.getOverview(role);
      setOverviewData(data);
    } catch (err) {
      console.error('Failed to load overview:', err);
    }
  };

  const handleSessionUpdated = (authRes) => {
    if (authRes && authRes.user) {
      setCurrentUser(authRes.user);
      setAuthToken(authRes.token);
      setTenantInfo({
        tenant_id: authRes.tenant_id,
        name: authRes.organization_name,
        industry: authRes.industry
      });
      setIsImpersonating(authRes.is_impersonating || false);
      setImpersonationInfo(authRes.impersonation_info || null);
      loadOverview(authRes.user.role);

      // If non-admin user is logged in, redirect away from admin console
      if (authRes.user.role !== 'Administrator' && activeNav === 'admin') {
        setActiveNav('overview');
      }
    }
  };

  const handleEndImpersonation = async () => {
    try {
      const res = await api.endImpersonation(authToken);
      if (res) {
        localStorage.setItem('intelgraph_token', res.token);
        handleSessionUpdated(res);
      }
    } catch (err) {
      alert('Failed to end impersonation session: ' + err.message);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem('intelgraph_token');
    setLoginModalOpen(true);
  };

  // Guard active nav against unauthorized admin access
  useEffect(() => {
    if (currentUser && currentUser.role !== 'Administrator' && activeNav === 'admin') {
      setActiveNav('overview');
    }
  }, [currentUser, activeNav]);

  // Keyboard shortcut for Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleSelectAsset = (tag) => {
    setSelectedAssetTag(tag);
    setActiveNav('assets');
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Platform Navigation Sidebar */}
      <Sidebar
        activeNav={activeNav}
        setActiveNav={(nav) => {
          if (nav === 'assets') {
            setSelectedAssetTag(null);
          }
          setActiveNav(nav);
          setMobileMenuOpen(false);
        }}
        actionCount={overviewData?.open_findings?.length || 0}
        currentUser={currentUser}
        tenantInfo={tenantInfo}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Safety Disclaimer Banner */}
        <SafetyDisclaimer />

        {/* Enterprise Topbar */}
        <Topbar
          currentUser={currentUser}
          tenantInfo={tenantInfo}
          isImpersonating={isImpersonating}
          impersonationInfo={impersonationInfo}
          onEndImpersonation={handleEndImpersonation}
          onOpenLoginModal={() => setLoginModalOpen(true)}
          onSignOut={handleSignOut}
          onToggleMobileMenu={() => setMobileMenuOpen(prev => !prev)}
          activeAsset={selectedAssetTag ? { 
            tag: selectedAssetTag, 
            name: selectedAssetTag   // actual name resolved by AssetProfile via API
          } : null}
          onOpenSearch={() => setSearchOpen(true)}
          onOpenChat={() => setChatOpen(true)}
          onReseedCompleted={() => {
            loadOverview(currentUser?.role);
            setSelectedAssetTag(null);
          }}
        />

        {/* Content Views */}
        <main className="flex-1 overflow-y-auto bg-slate-950/95">
          {activeNav === 'overview' && (
            <OverviewView
              overviewData={overviewData}
              currentRole={currentUser?.role || 'Maintenance Engineer'}
              onSelectAsset={handleSelectAsset}
              onNavigate={(nav) => setActiveNav(nav)}
            />
          )}

          {activeNav === 'assets' && (
            selectedAssetTag ? (
              <div className="space-y-2">
                <div className="px-6 pt-4">
                  <button
                    onClick={() => setSelectedAssetTag(null)}
                    className="text-xs text-slate-400 hover:text-brand-400 flex items-center gap-1 font-mono transition-colors"
                  >
                    ← Back to All Machines
                  </button>
                </div>
                <AssetProfile
                  assetTag={selectedAssetTag}
                  currentRole={currentUser?.role || 'Maintenance Engineer'}
                  onBack={() => setSelectedAssetTag(null)}
                  onOpenUpload={() => setOnboardingModalOpen(true)}
                  onOpenDocViewer={(id) => setDocViewerId(id)}
                />
              </div>
            ) : (
              <AssetDirectory
                onSelectAsset={(tag) => setSelectedAssetTag(tag)}
                onOpenNewAssetModal={() => setNewAssetModalOpen(true)}
                onOpenOnboardingModal={() => setOnboardingModalOpen(true)}
              />
            )
          )}

          {activeNav === 'actions' && (
            <ActionCenterView
              currentRole={currentUser?.role || 'Maintenance Engineer'}
              currentPersona={currentUser}
              onSelectAsset={handleSelectAsset}
            />
          )}

          {activeNav === 'knowledge' && (
            <KnowledgeView onSelectAsset={handleSelectAsset} />
          )}

          {activeNav === 'compliance' && (
            <ComplianceView
              currentRole={currentUser?.role || 'Maintenance Engineer'}
              currentPersona={currentUser}
              onSelectAsset={handleSelectAsset}
            />
          )}

          {activeNav === 'reports' && (
            <ReportsView
              onSelectAsset={handleSelectAsset}
              onOpenDocViewer={(id) => setDocViewerId(id)}
            />
          )}

          {activeNav === 'admin' && (
            <AdminConsoleView
              currentUser={currentUser}
              onSessionUpdated={handleSessionUpdated}
            />
          )}
        </main>
      </div>

      {/* Global Modals & Wizards */}
      <GlobalSearchModal
        isOpen={searchOpen}
        onClose={() => setSearchOpen(false)}
        onSelectAsset={handleSelectAsset}
        onOpenDocViewer={(id) => setDocViewerId(id)}
      />

      <GlobalChatModal
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        defaultAssetTag={selectedAssetTag || 'P-101'}
        currentRole={currentUser?.role || 'Maintenance Engineer'}
        siteName={currentUser?.plant_scope || 'Plant A'}
        onOpenDocViewer={(id) => setDocViewerId(id)}
      />

      <EnterpriseLoginModal
        isOpen={loginModalOpen}
        onClose={() => setLoginModalOpen(false)}
        onSuccess={handleSessionUpdated}
      />

      {newAssetModalOpen && (
        <NewAssetModal
          onClose={() => setNewAssetModalOpen(false)}
          onAssetCreated={(asset) => {
            setSelectedAssetTag(asset.tag);
            setActiveNav('assets');
            loadOverview(currentUser?.role);
          }}
        />
      )}

      {onboardingModalOpen && (
        <OnboardingWizardModal
          defaultAssetTag={selectedAssetTag || 'P-101'}
          onClose={() => setOnboardingModalOpen(false)}
          onCompleted={(tag) => {
            setSelectedAssetTag(tag);
            setActiveNav('assets');
            loadOverview(currentUser?.role);
          }}
        />
      )}

      {docViewerId && (
        <DocumentViewerModal
          documentId={docViewerId}
          onClose={() => setDocViewerId(null)}
        />
      )}
    </div>
  );
}
