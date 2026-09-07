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
import SettingsView from './components/settings/SettingsView';
import NewAssetModal from './components/wizards/NewAssetModal';
import OnboardingWizardModal from './components/wizards/OnboardingWizardModal';
import DocumentViewerModal from './components/documents/DocumentViewerModal';
import GlobalSearchModal from './components/search/GlobalSearchModal';
import GlobalChatModal from './components/chat/GlobalChatModal';
import { api } from './services/api';

export default function App() {
  const [activeNav, setActiveNav] = useState('overview');
  const [selectedAssetTag, setSelectedAssetTag] = useState('P-101');
  const [currentRole, setCurrentRole] = useState('Maintenance Engineer');
  const [overviewData, setOverviewData] = useState(null);

  // Modals
  const [searchOpen, setSearchOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [newAssetModalOpen, setNewAssetModalOpen] = useState(false);
  const [onboardingModalOpen, setOnboardingModalOpen] = useState(false);
  const [docViewerId, setDocViewerId] = useState(null);

  const loadOverview = async (role = currentRole) => {
    try {
      const data = await api.getOverview(role);
      setOverviewData(data);
    } catch (err) {
      console.error('Failed to load overview:', err);
    }
  };

  useEffect(() => {
    loadOverview(currentRole);
  }, [currentRole]);

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
      {/* 7-Item Navigation Sidebar */}
      <Sidebar
        activeNav={activeNav}
        setActiveNav={(nav) => {
          setActiveNav(nav);
        }}
        actionCount={overviewData?.open_findings?.length || 0}
      />

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Safety Rule #17 Banner */}
        <SafetyDisclaimer />

        {/* Dynamic Topbar */}
        <Topbar
          currentRole={currentRole}
          setCurrentRole={setCurrentRole}
          activeAsset={selectedAssetTag ? { tag: selectedAssetTag, name: selectedAssetTag === 'P-101' ? 'Centrifugal Water Injection Pump' : selectedAssetTag } : null}
          onOpenSearch={() => setSearchOpen(true)}
          onOpenChat={() => setChatOpen(true)}
          onReseedCompleted={() => {
            loadOverview(currentRole);
            setSelectedAssetTag('P-101');
          }}
        />

        {/* Content Views */}
        <main className="flex-1 overflow-y-auto bg-slate-950/95">
          {activeNav === 'overview' && (
            <OverviewView
              overviewData={overviewData}
              currentRole={currentRole}
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
                    ← Back to All Assets Directory
                  </button>
                </div>
                <AssetProfile
                  assetTag={selectedAssetTag}
                  currentRole={currentRole}
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
            <ActionCenterView onSelectAsset={handleSelectAsset} />
          )}

          {activeNav === 'knowledge' && (
            <KnowledgeView onSelectAsset={handleSelectAsset} />
          )}

          {activeNav === 'compliance' && (
            <ComplianceView onSelectAsset={handleSelectAsset} />
          )}

          {activeNav === 'reports' && (
            <ReportsView
              onSelectAsset={handleSelectAsset}
              onOpenDocViewer={(id) => setDocViewerId(id)}
            />
          )}

          {activeNav === 'settings' && (
            <SettingsView
              currentRole={currentRole}
              setCurrentRole={setCurrentRole}
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
        onOpenDocViewer={(id) => setDocViewerId(id)}
      />

      {newAssetModalOpen && (
        <NewAssetModal
          onClose={() => setNewAssetModalOpen(false)}
          onAssetCreated={(asset) => {
            setSelectedAssetTag(asset.tag);
            setActiveNav('assets');
            loadOverview(currentRole);
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
            loadOverview(currentRole);
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
