import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Layers, 
  Wrench, 
  Activity, 
  AlertCircle, 
  FileText, 
  MessageSquare, 
  History, 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles, 
  Calendar, 
  Send,
  ExternalLink,
  ChevronRight,
  Settings
} from 'lucide-react';
import { api } from '../../services/api';
import TabOverview from './TabOverview';
import TabKnowledgeMap from './TabKnowledgeMap';
import TabMaintenance from './TabMaintenance';
import TabTelemetry from './TabTelemetry';
import TabFindings from './TabFindings';
import TabDocuments from './TabDocuments';
import TabNotes from './TabNotes';
import ManageMachineModal from './ManageMachineModal';
import EvidenceDrawer from '../common/EvidenceDrawer';

export default function AssetProfile({ 
  assetTag, 
  currentRole, 
  onBack, 
  onOpenUpload,
  onOpenDocViewer 
}) {
  const [asset, setAsset] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [maintenanceData, setMaintenanceData] = useState(null);
  const [notes, setNotes] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [manageModalOpen, setManageModalOpen] = useState(false);

  // Evidence Drawer State
  const [evidenceDrawerOpen, setEvidenceDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  // Scoped AI Chat
  const [chatQuery, setChatQuery] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatResponse, setChatResponse] = useState(null);

  const loadAssetData = async () => {
    setLoading(true);
    try {
      const [assetData, maintData, notesData, auditData] = await Promise.all([
        api.getAsset(assetTag),
        api.getMaintenance(assetTag),
        api.getNotes(assetTag),
        api.getAuditLogs(assetTag)
      ]);
      setAsset(assetData);
      setMaintenanceData(maintData);
      setNotes(notesData);
      setAuditLogs(auditData);
    } catch (err) {
      console.error('Failed to load asset profile:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssetData();
    setChatResponse(null);
  }, [assetTag]);

  const handleQuickChat = async (queryText) => {
    const q = queryText || chatQuery;
    if (!q.trim()) return;
    setChatLoading(true);
    try {
      const res = await api.chat(q, assetTag, currentRole, true);
      setChatResponse(res);
    } catch (err) {
      alert('Failed to query knowledge brain: ' + err.message);
    } finally {
      setChatLoading(false);
    }
  };

  const handleOpenEvidenceFromCitations = (citations) => {
    const list = citations.map(c => ({
      document_name: c.document_name,
      document_id: c.document_id,
      date: 'Verified Record',
      page: c.page_number,
      section: c.section_title,
      status: 'Approved',
      excerpt: c.excerpt || 'Approved record cited in knowledge synthesis.'
    }));
    setSelectedEvidence(list);
    setEvidenceDrawerOpen(true);
  };

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-400">
        <div className="w-8 h-8 border-2 border-brand-400 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        Synthesizing knowledge brain for {assetTag}...
      </div>
    );
  }

  if (!asset) {
    return (
      <div className="p-12 text-center text-slate-400">
        Machine profile for {assetTag} not found.
      </div>
    );
  }

  // 8 Lightweight Tabs
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Layers },
    { id: 'knowledge', label: 'Knowledge Graph', icon: Cpu },
    { id: 'maintenance', label: 'Maintenance', icon: Wrench },
    { id: 'telemetry', label: 'Telemetry', icon: Activity },
    { id: 'findings', label: 'Findings', icon: AlertCircle, count: asset.open_findings_count },
    { id: 'documents', label: 'Documents', icon: FileText, count: asset.document_count },
    { id: 'notes', label: 'Notes', icon: MessageSquare, count: notes.length },
    { id: 'activity', label: 'Audit Log', icon: History },
  ];

  // Coverage count derived from actual completeness_breakdown — NOT hardcoded
  const completenessBreakdown = asset.completeness_breakdown || [];
  const coverageCount = completenessBreakdown.filter(i => i.status === 'completed').length;
  const coverageTotal = completenessBreakdown.length || 8;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* 1. MACHINE IDENTITY HEADER */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="font-mono text-sm font-bold text-brand-400">
              {asset.tag}
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              {asset.name}
            </h1>
            <div className="flex items-center gap-2 pt-0.5">
              <span className={`flex items-center gap-1.5 text-xs font-semibold ${
                asset.status === 'Operational' ? 'text-emerald-400' : 'text-red-400'
              }`}>
                <span className={`w-2 h-2 rounded-full ${
                  asset.status === 'Operational' ? 'bg-emerald-400' : 'bg-red-400'
                }`}></span>
                {asset.status}
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-400 text-xs">{asset.manufacturer} {asset.model}</span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-400 text-xs">{asset.plant} / {asset.area}</span>
            </div>
          </div>

          {/* Machine Profile Signals */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {asset.open_findings_count > 0 && (
              <span className="px-3 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 font-medium flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                <span>{asset.open_findings_count} Finding</span>
              </span>
            )}

            <span className="px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-mono">
              <strong className="text-brand-400">{coverageCount}/{coverageTotal}</strong> Knowledge Areas
            </span>

            <span className="px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>Next Maint: <strong className="text-slate-200">
                {maintenanceData?.next_maintenance
                  ? maintenanceData.next_maintenance
                  : maintenanceData?.last_maintenance
                    ? 'Schedule pending'
                    : 'Not scheduled'}
              </strong></span>
            </span>

            <button
              onClick={() => setManageModalOpen(true)}
              className="px-3 py-1 rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 hover:text-white font-medium flex items-center gap-1.5 transition shadow-sm"
              title="Manage Machine Lifecycle (Edit, Archive, Restore, Delete)"
            >
              <Settings className="w-3.5 h-3.5 text-brand-400" />
              <span>Manage Machine</span>
            </button>
          </div>
        </div>

        {/* Archived Banner Notice */}
        {asset.status === 'Archived' && (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-amber-300">Machine is in Archived State</h4>
                <p className="text-xs text-amber-200/80">
                  This asset is preserved for historical reference and statutory compliance. It does not appear in active operational queues.
                </p>
              </div>
            </div>
            <button
              onClick={async () => {
                try {
                  await api.restoreMachine(asset.tag);
                  loadAssetData();
                } catch (e) {
                  alert('Failed to restore: ' + e.message);
                }
              }}
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shrink-0 transition"
            >
              Restore Machine
            </button>
          </div>
        )}

        {/* 8 Lightweight Tabs Strip */}
        <div className="flex items-center gap-1.5 overflow-x-auto border-t border-slate-800 pt-3">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/20'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-300'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. TAB CONTENT VIEWS */}
      {activeTab === 'overview' && (
        <TabOverview
          asset={asset}
          maintenanceData={maintenanceData}
          onOpenDocViewer={onOpenDocViewer}
        />
      )}

      {activeTab === 'knowledge' && (
        <TabKnowledgeMap
          assetTag={assetTag}
          onOpenDocViewer={onOpenDocViewer}
        />
      )}

      {activeTab === 'maintenance' && (
        <TabMaintenance
          assetTag={assetTag}
          maintenanceData={maintenanceData}
        />
      )}

      {activeTab === 'telemetry' && (
        <TabTelemetry assetTag={assetTag} />
      )}

      {activeTab === 'findings' && (
        <TabFindings
          assetTag={assetTag}
          findings={maintenanceData?.findings || []}
          onOpenDocViewer={onOpenDocViewer}
        />
      )}

      {activeTab === 'documents' && (
        <TabDocuments
          assetTag={assetTag}
          onOpenUpload={onOpenUpload}
        />
      )}

      {activeTab === 'notes' && (
        <TabNotes
          assetTag={assetTag}
          notes={notes}
          onNoteAdded={loadAssetData}
          currentRole={currentRole}
        />
      )}

      {activeTab === 'activity' && (
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              <History className="w-4 h-4 text-brand-400" />
              <span>Immutable Asset Audit Trail</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Chronological records of actual document uploads, confirmations, and governance updates
            </p>
          </div>

          <div className="space-y-2.5">
            {auditLogs.map((log) => (
              <div key={log.event_id} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span className="font-semibold text-brand-400">{log.action}</span>
                  <span className="text-slate-400">{log.timestamp}</span>
                </div>
                <p className="text-slate-200 break-words">
                  {typeof log.details === 'object' ? (log.details?.note || log.details?.reason || JSON.stringify(log.details)) : log.details}
                </p>
                <div className="text-[10px] text-slate-400 font-mono pt-1">
                  Actor: {log.user} ({log.role}) • Target: {log.target_type} [{log.target_id}]
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. GROUNDED DECISION-SUPPORT ASSISTANT (Structured Answers) */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-400" />
            <h3 className="font-bold text-sm text-white">Ask IntelGraph AI About {asset.tag}</h3>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Grounded in Approved Records</span>
          </span>
        </div>

        {/* Question Chips — dynamic per asset.tag, no hardcoded machine references */}
        <div className="flex flex-wrap items-center gap-2">
          {[
            `What is the maintenance history of ${asset.tag}?`,
            `Has ${asset.tag} experienced any bearing failures?`,
            `What is the recommended lubrication specification for ${asset.tag}?`,
            `What are the key findings from the last inspection of ${asset.tag}?`
          ].map((prompt, i) => (
            <button
              key={i}
              onClick={() => {
                setChatQuery(prompt);
                handleQuickChat(prompt);
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-brand-300 text-[11px] font-medium border border-slate-700/60 transition-all"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Query Input */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={chatQuery}
            onChange={(e) => setChatQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuickChat()}
            placeholder={`Ask question about ${asset.tag} records, procedures, or vibration limits...`}
            className="flex-1 px-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-brand-500"
          />
          <button
            onClick={() => handleQuickChat()}
            disabled={chatLoading}
            className="px-4 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-brand-500/20 disabled:opacity-50"
          >
            {chatLoading ? (
              <span className="animate-spin w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            <span>Query</span>
          </button>
        </div>

        {/* Structured AI Response Card */}
        {chatResponse && (
          <div className="p-4 rounded-xl bg-slate-950 border border-brand-500/30 space-y-3 text-xs animate-in fade-in duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="font-semibold text-brand-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                Structured Operational Decision Support
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                {chatResponse.confidence} Confidence • Grounded
              </span>
            </div>

            {/* Answer & Why */}
            <div className="space-y-2">
              <div className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
                ANSWER
              </div>
              <p className="text-sm font-sans text-slate-100 leading-relaxed font-medium">
                {chatResponse.answer}
              </p>
            </div>

            {/* Citations / Evidence Button */}
            {chatResponse.citations?.length > 0 && (
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-slate-400 text-xs">
                  Evidence: <strong className="text-white">{chatResponse.citations.length} verified records cited</strong>
                </span>
                <button
                  onClick={() => handleOpenEvidenceFromCitations(chatResponse.citations)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-brand-400 hover:text-brand-300 font-semibold text-xs border border-slate-700 transition-all flex items-center gap-1.5"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>View Evidence</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Evidence Drawer */}
      <EvidenceDrawer
        isOpen={evidenceDrawerOpen}
        onClose={() => setEvidenceDrawerOpen(false)}
        evidenceData={selectedEvidence}
        onOpenDocViewer={onOpenDocViewer}
      />

      {/* Manage Machine Lifecycle Modal */}
      <ManageMachineModal
        isOpen={manageModalOpen}
        onClose={() => setManageModalOpen(false)}
        asset={asset}
        currentRole={currentRole}
        onMachineUpdated={(updated) => {
          setAsset(updated);
        }}
        onMachineDeleted={() => {
          if (onBack) onBack();
        }}
      />
    </div>
  );
}
